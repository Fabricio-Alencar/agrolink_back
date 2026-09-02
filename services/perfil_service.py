import os
import shutil
from uuid import uuid4
from werkzeug.security import generate_password_hash

from database import SessionLocal
from models.usuario import Usuario

# Caminho da pasta onde as fotos de perfil serão salvas fisicamente
UPLOAD_FOLDER_PERFIL = os.path.join('static', 'uploads', 'perfis')


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

        # Tratamento para Localização (cidade e estado)
        # Como no HTML está um campo só ("Cidade, Estado"), você pode precisar dividir no JS antes de mandar, 
        # ou separar aqui no Python caso o front envie a string inteira.
        usuario.cidade = data.get('cidade', usuario.cidade)
        usuario.estado = data.get('estado', usuario.estado)

        # 3. ATUALIZA SENHA (Se o usuário digitou uma nova diferente dos pontinhos do placeholder)
        nova_senha = data.get('senha')

        if nova_senha and nova_senha.strip() != "" and nova_senha != "••••••••":
            usuario.senha = generate_password_hash(nova_senha)

        # 4. PROCESSA NOVA FOTO DE PERFIL (SE ENVIADA)
        if arquivo_foto:
            # a) Apaga a foto antiga do disco (se não for a imagem padrão user.webp)
            if getattr(usuario, 'foto_perfil', None) and "user.webp" not in usuario.foto_perfil:
                caminho_antigo = os.path.join('static', usuario.foto_perfil)

                if os.path.exists(caminho_antigo):
                    os.remove(caminho_antigo)

            # b) Salva a nova foto
            os.makedirs(UPLOAD_FOLDER_PERFIL, exist_ok=True)

            extensao = os.path.splitext(arquivo_foto.filename)[1]
            nome_arquivo = f"{uuid4().hex}{extensao}"

            caminho_completo = os.path.join(UPLOAD_FOLDER_PERFIL, nome_arquivo)
            with open(caminho_completo, "wb") as arquivo:
               shutil.copyfileobj(arquivo_foto.file, arquivo)

            # c) Atualiza o caminho no objeto do banco
            usuario.foto_perfil = f"uploads/perfis/{nome_arquivo}"

        # 5. SALVA NO BANCO
        try:
            db.commit()
            db.refresh(usuario)

            return usuario

        except Exception as e:
            db.rollback()
            raise Exception(f"Erro ao atualizar perfil no banco de dados: {str(e)}")

    finally:
        db.close()


# =========================
# EXCLUIR CONTA DE USUÁRIO
# =========================
def excluir_conta_usuario(user_id):
    db = SessionLocal()

    try:
        # 1. BUSCA O USUÁRIO NO BANCO
        usuario = db.get(Usuario, user_id)

        if not usuario:
            raise Exception("Usuário não encontrado.")

        try:
            # 2. REMOVE A FOTO DE PERFIL FÍSICA (se não for a padrão)
            if getattr(usuario, 'foto_perfil', None) and "user.webp" not in usuario.foto_perfil:
                caminho_imagem = os.path.join('static', usuario.foto_perfil)

                if os.path.exists(caminho_imagem):
                    os.remove(caminho_imagem)

            # Nota: Dependendo de como estão configuradas as suas Foreign Keys (cascade)
            # deletar o usuário pode já deletar os produtos e negociações dele automaticamente.

            # 3. EXCLUI O USUÁRIO
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
