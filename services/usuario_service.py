import re
import logging
from werkzeug.security import generate_password_hash, check_password_hash
from models import db
from models.usuario import Usuario

# =========================
# FUNÇÕES AUXILIARES E DE SEGURANÇA
# =========================

def sanitizar_input(valor):
    """Remove espaços em branco nas extremidades e trata valores nulos."""
    if isinstance(valor, str):
        return valor.strip()
    return valor

def validar_email(email):
    """Valida o formato do e-mail usando Regex."""
    if not email:
        return False
    padrao = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(padrao, email) is not None

def hash_senha(senha):
    """Gera um hash seguro da senha usando pbkdf2:sha256 por padrão."""
    return generate_password_hash(senha)

def verificar_senha(senha_hash, senha_texto):
    """Compara o hash salvo no banco com a senha fornecida."""
    return check_password_hash(senha_hash, senha_texto)


# =========================
# CADASTRO DE USUÁRIO
# =========================

def criar_usuario(data):
    try:
        # Sanitização e extração segura
        nome = sanitizar_input(data.get("nome"))
        email = sanitizar_input(data.get("email"))
        senha = sanitizar_input(data.get("senha"))
        tipo = sanitizar_input(data.get("tipo"))
        telefone = sanitizar_input(data.get("telefone"))
        estado = sanitizar_input(data.get("estado"))
        cidade = sanitizar_input(data.get("cidade"))

        # 1. Validação de campos obrigatórios
        if not all([nome, email, senha, tipo]):
            raise ValueError("Dados obrigatórios incompletos.")

        # 2. Validação de formato de e-mail
        if not validar_email(email):
            raise ValueError("Formato de e-mail inválido.")

        # 3. Prevenção contra duplicidade de e-mail
        # O uso do SQLAlchemy ORM (.filter_by) protege contra SQL Injection
        if Usuario.query.filter_by(email=email).first():
            raise ValueError("Não foi possível realizar o cadastro. Dados inválidos")

        # 4. Geração do Hash da Senha
        senha_hash = hash_senha(senha)

        # 5. Criação do Objeto Usuário
        usuario = Usuario(
            nome=nome,
            email=email,
            telefone=telefone,
            estado=estado,
            cidade=cidade,
            senha=senha_hash,
            tipo=tipo,
            avaliacao=5.0
        )

        db.session.add(usuario)
        db.session.commit()

        return usuario

    except ValueError as ve:
        # Erros esperados e controlados (validações)
        raise ve
    except Exception as e:
        # Reversão do banco em caso de erro inesperado e log de segurança
        db.session.rollback()
        logging.error(f"Erro interno no cadastro de usuário: {e}")
        raise Exception("Não foi possível processar o cadastro no momento.")


# =========================
# LOGIN
# =========================

def login_usuario(data):
    try:
        # Sanitização da entrada
        email = sanitizar_input(data.get("email"))
        senha = sanitizar_input(data.get("senha"))
        tipo_esperado = sanitizar_input(data.get("tipo"))

        # 1. Validação básica de campos
        if not email or not senha:
            raise ValueError("Credenciais inválidas.")

        if not validar_email(email):
            raise ValueError("Credenciais inválidas.")

        # 2. Busca do usuário de forma segura via ORM
        usuario = Usuario.query.filter_by(email=email).first()

        # 3. Alertas Genéricos: Se o usuário não existir, informamos "Credenciais inválidas"
        if not usuario:
            raise ValueError("Credenciais inválidas.")

        # 4. Verificação segura do hash
        if not verificar_senha(usuario.senha, senha):
            raise ValueError("Credenciais inválidas.")

        # 5. Verificação do tipo de usuário (regra de negócio)
        if tipo_esperado and tipo_esperado != usuario.tipo:
            raise ValueError("Credenciais inválidas.")

        return usuario

    except ValueError as ve:
        # Levanta as mensagens genéricas de "Credenciais inválidas"
        raise ve
    except Exception as e:
        # Previne o vazamento da stack trace em caso de falha de banco/sistema
        logging.error(f"Erro interno durante login: {e}")
        raise Exception("Não foi possível realizar o login.")