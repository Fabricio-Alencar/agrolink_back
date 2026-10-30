from uuid import uuid4

from sqlalchemy import or_, func
from werkzeug.security import generate_password_hash

from database import SessionLocal
from models.usuario import Usuario, TAMANHO_MAXIMO_NOME
from models.produto import Produto
from models.negociacao import Negociacao

from services.azure_storage_service import (
    upload_arquivo,
    deletar_arquivo,
    CONTAINER_USUARIOS
)

from services.cache_service import redis_client


# Pedidos nesses status não impedem a exclusão da conta
STATUS_ENCERRADOS = ("cancelado", "recusado", "finalizado")


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

        novo_nome = (data.get("nome") or "").strip()

        if len(novo_nome) > TAMANHO_MAXIMO_NOME:
            raise Exception(f"O nome pode ter no máximo {TAMANHO_MAXIMO_NOME} caracteres.")

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

        # Só pode excluir se nenhum pedido (comprando ou vendendo) estiver em andamento
        pedidos_em_andamento = db.query(Negociacao).filter(
            or_(
                Negociacao.comprador_id == usuario.id,
                Negociacao.vendedor_id == usuario.id
            ),
            func.lower(func.coalesce(Negociacao.status, "pendente")).notin_(
                STATUS_ENCERRADOS
            )
        ).count()

        if pedidos_em_andamento:
            raise Exception(
                f"Você ainda tem {pedidos_em_andamento} "
                f"{'pedido' if pedidos_em_andamento == 1 else 'pedidos'} em andamento "
                "(pendente, aceito ou entregue). Finalize ou cancele antes de excluir a conta."
            )

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

            # A conta não é apagada: os pedidos antigos continuam no histórico
            # da outra pessoa, com o nome e o aviso "conta excluída".
            # Fica guardado só o nome e o tipo; o resto é apagado.
            # E-mail e senha não podem ficar vazios no banco, então viram
            # valores aleatórios (ninguém consegue entrar e o e-mail fica livre).
            usuario.conta_excluida = True
            usuario.email = f"excluido_{usuario.id}_{uuid4().hex[:8]}@conta-excluida.invalid"
            usuario.senha = generate_password_hash(uuid4().hex)
            usuario.telefone = None
            usuario.cidade = None
            usuario.estado = None
            usuario.foto_perfil = "user.webp"

            # Produtos saem do marketplace, mas continuam ligados aos pedidos antigos
            for produto in db.query(Produto).filter(Produto.produtor_id == usuario.id):
                produto.status = "excluido"

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
