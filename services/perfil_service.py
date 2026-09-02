from uuid import uuid4

from werkzeug.security import generate_password_hash

from database import SessionLocal
from models.usuario import Usuario

from services.azure_storage_service import (
    upload_arquivo,
    CONTAINER_USUARIOS
)


# =========================
# BUSCAR PERFIL DO USUÁRIO
# =========================
def obter_perfil_usuario(user_id):
    db = SessionLocal()

    try:
        usuario = db.get(Usuario, user_id)

        if not usuario:
            raise Exception("Usuário não encontrado.")

        return usuario

    finally:
        db.close()


# =========================
# ATUALIZAR DADOS DO PERFIL E FOTO
# =========================
def atualizar_perfil_usuario(user_id, data, arquivo_foto):
    db = SessionLocal()

    try:
        # 1. BUSCA O USUÁRIO NO BANCO
        usuario = db.get(Usuario, user_id)

        if not usuario:
            raise Exception("Usuário não encontrado.")

        # 2. ATUALIZA CAMPOS DE TEXTO BÁSICOS
        usuario.nome = data.get('nome', usuario.nome)
        usuario.email = data.get('email', usuario.email)
        usuario.telefone = data.get('telefone', usuario.telefone)

        # Localização
        usuario.cidade = data.get('cidade', usuario.cidade)
        usuario.estado = data.get('estado', usuario.estado)

        # 3. ATUALIZA SENHA
        nova_senha = data.get('senha')

        if (
            nova_senha
            and nova_senha.strip() != ""
            and nova_senha != "••••••••"
        ):
            usuario.senha = generate_password_hash(nova_senha)

        # 4. PROCESSA NOVA FOTO DE PERFIL
        if arquivo_foto:

            # Pega a extensão do arquivo
            extensao = ""

            if (
                arquivo_foto.filename
                and "." in arquivo_foto.filename
            ):
                extensao = "." + arquivo_foto.filename.rsplit(
                    ".",
                    1
                )[1].lower()

            # Gera nome único
            nome_blob = f"{uuid4().hex}{extensao}"

            # Envia diretamente para o Azure Blob
            upload_arquivo(
                arquivo_foto.file,
                nome_blob,
                CONTAINER_USUARIOS
            )

            # Salva somente o nome do Blob no banco
            usuario.foto_perfil = nome_blob

        # 5. SALVA NO BANCO
        try:
            db.commit()
            db.refresh(usuario)

            return usuario

        except Exception as e:
            db.rollback()

            raise Exception(
                f"Erro ao atualizar perfil no banco de dados: {str(e)}"
            )

    finally:
        db.close()


# =========================
# EXCLUIR CONTA DE USUÁRIO
# =========================
def excluir_conta_usuario(user_id):
    db = SessionLocal()

    try:
        # 1. BUSCA O USUÁRIO
        usuario = db.get(Usuario, user_id)

        if not usuario:
            raise Exception("Usuário não encontrado.")

        try:
            # 2. EXCLUI O USUÁRIO
            #
            # Por enquanto não removemos a imagem do Azure.
            # Isso será feito depois com uma função específica
            # para deletar o Blob.
            db.delete(usuario)

            db.commit()

            print(
                f"✅ SUCESSO: Conta do usuário {user_id} excluída."
            )

            return True

        except Exception as e:
            db.rollback()

            print(
                "\n❌ [ERRO AO EXCLUIR CONTA]:",
                str(e)
            )

            raise Exception(
                "Erro ao excluir conta no banco de dados. "
                "Verifique restrições de chave estrangeira."
            )

    finally:
        db.close()