from uuid import uuid4
from werkzeug.security import generate_password_hash
from database import SessionLocal
from models.usuario import Usuario
from services.azure_storage_service import (
    upload_arquivo,
    deletar_arquivo,
    CONTAINER_USUARIOS
)

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

        usuario.nome = data.get('nome', usuario.nome)
        usuario.email = data.get('email', usuario.email)
        usuario.telefone = data.get('telefone', usuario.telefone)
        usuario.cidade = data.get('cidade', usuario.cidade)
        usuario.estado = data.get('estado', usuario.estado)

        nova_senha = data.get('senha')
        if nova_senha and nova_senha.strip() != "" and nova_senha != "••••••••":
            usuario.senha = generate_password_hash(nova_senha)

        if arquivo_foto:
            extensao = ""
            if arquivo_foto.filename and "." in arquivo_foto.filename:
                extensao = "." + arquivo_foto.filename.rsplit(".", 1)[1].lower()

            novo_nome_blob = f"{uuid4().hex}{extensao}"

            upload_arquivo(arquivo_foto.file, novo_nome_blob, CONTAINER_USUARIOS)
            usuario.foto_perfil = novo_nome_blob

            if foto_antiga and foto_antiga != "user.webp" and not foto_antiga.startswith("http://") and not foto_antiga.startswith("https://"):
                try:
                    deletar_arquivo(foto_antiga, CONTAINER_USUARIOS)
                except Exception as e:
                    print("⚠️ Não foi possível excluir a foto antiga:", str(e))

        try:
            db.commit()
            db.refresh(usuario)
            print(f"✅ SUCESSO: Perfil do usuário {user_id} atualizado.")
            return usuario
        except Exception as e:
            db.rollback()
            raise Exception(f"Erro ao atualizar perfil no banco de dados: {str(e)}")

    finally:
        db.close()

def excluir_conta_usuario(user_id):
    db = SessionLocal()
    try:
        usuario = db.get(Usuario, user_id)
        if not usuario:
            raise Exception("Usuário não encontrado.")

        foto_perfil = usuario.foto_perfil

        if foto_perfil and foto_perfil != "user.webp" and not foto_perfil.startswith("http://") and not foto_perfil.startswith("https://"):
            try:
                deletar_arquivo(foto_perfil, CONTAINER_USUARIOS)
                print(f"🗑️ Foto de perfil do usuário {user_id} removida do Azure.")
            except Exception as e:
                print("⚠️ Não foi possível excluir a foto de perfil:", str(e))

        try:
            db.delete(usuario)
            db.commit()
            print(f"✅ SUCESSO: Conta do usuário {user_id} excluída.")
            return True
        except Exception as e:
            db.rollback()
            print("\n❌ [ERRO AO EXCLUIR CONTA]:", str(e))
            raise Exception("Erro ao excluir conta no banco de dados. Verifique restrições de chave estrangeira.")

    finally:
        db.close()