from uuid import uuid4

from werkzeug.security import generate_password_hash

from database import SessionLocal
from models.usuario import Usuario

from services.azure_storage_service import (
    upload_arquivo,
    deletar_arquivo,
    CONTAINER_USUARIOS
)

from services.cache_service import redis_client


def obter_perfil_usuario(user_id):
    db = SessionLocal()

    try:
        usuario = db.get(Usuario, user_id)

        if not usuario:
            raise Exception("Usuário não encontrado.")

        return usuario

    finally:
        db.close()


def atualizar_perfil_usuario(user_id, data, arquivo_foto):
    db = SessionLocal()

    try:
        usuario = db.get(Usuario, user_id)

        if not usuario:
            raise Exception("Usuário não encontrado.")

        foto_antiga = usuario.foto_perfil

        # Atualizar os dados gerais do usuário
        usuario.nome = data.get("nome", usuario.nome)
        usuario.email = data.get("email", usuario.email)
        usuario.telefone = data.get("telefone", usuario.telefone)
        usuario.cidade = data.get("cidade", usuario.cidade)
        usuario.estado = data.get("estado", usuario.estado)

        # Atualizar a senha, caso tenha sido informada
        nova_senha = data.get("senha")

        if (
            nova_senha
            and nova_senha.strip() != ""
            and nova_senha != "••••••••"
        ):
            usuario.senha = generate_password_hash(nova_senha)

        # Atualizar a foto de perfil, caso um arquivo tenha sido enviado
        if arquivo_foto:
            extensao = ""

            if arquivo_foto.filename and "." in arquivo_foto.filename:
                extensao = "." + arquivo_foto.filename.rsplit(".", 1)[1].lower()

            novo_nome_blob = f"{uuid4().hex}{extensao}"

            upload_arquivo(
                arquivo_foto.file,
                novo_nome_blob,
                CONTAINER_USUARIOS
            )

            usuario.foto_perfil = novo_nome_blob

            # Excluir a foto anterior, se houver
            if (
                foto_antiga
                and foto_antiga != "user.webp"
                and not foto_antiga.startswith("http://")
                and not foto_antiga.startswith("https://")
            ):
                try:
                    deletar_arquivo(
                        foto_antiga,
                        CONTAINER_USUARIOS
                    )

                except Exception as e:
                    print(
                        "⚠️ Não foi possível excluir a foto antiga:",
                        str(e)
                    )

        # Salvar as alterações no banco de dados
        try:
            db.commit()
            db.refresh(usuario)

        except Exception as e:
            db.rollback()

            print(
                "\n❌ [ERRO AO SALVAR PERFIL NO BANCO]:",
                repr(e)
            )

            raise Exception(
                f"Erro ao atualizar perfil no banco de dados: {str(e)}"
            )

        # Invalidar o cache separadamente do salvamento do perfil
        if usuario.tipo == "produtor":
            try:
                redis_client.delete("marketplace")

            except Exception as e:
                print(
                    "\n⚠️ [ERRO AO INVALIDAR CACHE DO MARKETPLACE]:",
                    repr(e)
                )

        print(
            f"✅ SUCESSO: Perfil do usuário {user_id} atualizado."
        )

        return usuario

    finally:
        db.close()


def excluir_conta_usuario(user_id):
    db = SessionLocal()

    try:
        usuario = db.get(Usuario, user_id)

        if not usuario:
            raise Exception("Usuário não encontrado.")

        foto_perfil = usuario.foto_perfil

        # Excluir a foto de perfil do Azure, se houver
        if (
            foto_perfil
            and foto_perfil != "user.webp"
            and not foto_perfil.startswith("http://")
            and not foto_perfil.startswith("https://")
        ):
            try:
                deletar_arquivo(
                    foto_perfil,
                    CONTAINER_USUARIOS
                )

                print(
                    f"🗑️ Foto de perfil do usuário {user_id} removida do Azure."
                )

            except Exception as e:
                print(
                    "⚠️ Não foi possível excluir a foto de perfil:",
                    str(e)
                )

        try:
            tipo_usuario = usuario.tipo

            db.delete(usuario)
            db.commit()

            # Invalidar o cache do Marketplace se o usuário excluído for produtor
            if tipo_usuario == "produtor":
                try:
                    redis_client.delete("marketplace")

                except Exception as e:
                    print(
                        "\n⚠️ [ERRO AO INVALIDAR CACHE DO MARKETPLACE]:",
                        repr(e)
                    )

            print(
                f"✅ SUCESSO: Conta do usuário {user_id} excluída."
            )

            return True

        except Exception as e:
            db.rollback()

            print(
                "\n❌ [ERRO AO EXCLUIR CONTA]:",
                repr(e)
            )

            raise Exception(
                "Erro ao excluir conta no banco de dados. "
                "Verifique restrições de chave estrangeira."
            )

    finally:
        db.close()
