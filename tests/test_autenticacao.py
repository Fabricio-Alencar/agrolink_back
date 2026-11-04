import pytest

from werkzeug.security import check_password_hash

from services.usuario_service import (
    criar_usuario,
    login_usuario
)


@pytest.fixture
def dados_usuario():
    return {
        "nome": "Usuário Teste",
        "email": "teste@exemplo.com",
        "senha": "SenhaSegura123!",
        "tipo": "produtor",
        "telefone": "11999999999",
        "estado": "SP",
        "cidade": "São Paulo"
    }


class TestCadastro:

    def test_cadastro_com_dados_validos(
        self,
        banco_teste,
        dados_usuario
    ):
        usuario = criar_usuario(dados_usuario)

        assert usuario.id is not None
        assert usuario.nome == dados_usuario["nome"]
        assert usuario.email == dados_usuario["email"]
        assert usuario.tipo == dados_usuario["tipo"]

    def test_senha_e_armazenada_como_hash(
        self,
        banco_teste,
        dados_usuario
    ):
        usuario = criar_usuario(dados_usuario)

        assert usuario.senha != dados_usuario["senha"]

        assert check_password_hash(
            usuario.senha,
            dados_usuario["senha"]
        )

    def test_rejeita_email_duplicado(
        self,
        banco_teste,
        dados_usuario
    ):
        criar_usuario(dados_usuario)

        with pytest.raises(ValueError):
            criar_usuario(dados_usuario)

    def test_rejeita_campos_obrigatorios_vazios(
        self,
        banco_teste,
        dados_usuario
    ):
        dados_usuario["senha"] = ""

        with pytest.raises(ValueError):
            criar_usuario(dados_usuario)


class TestLogin:

    def test_login_com_credenciais_validas(
        self,
        banco_teste,
        dados_usuario
    ):
        criar_usuario(dados_usuario)

        usuario = login_usuario({
            "email": dados_usuario["email"],
            "senha": dados_usuario["senha"],
            "tipo": dados_usuario["tipo"]
        })

        assert usuario.email == dados_usuario["email"]

    def test_login_com_senha_incorreta(
        self,
        banco_teste,
        dados_usuario
    ):
        criar_usuario(dados_usuario)

        with pytest.raises(ValueError):
            login_usuario({
                "email": dados_usuario["email"],
                "senha": "SenhaIncorreta123!",
                "tipo": dados_usuario["tipo"]
            })

    def test_login_com_email_inexistente(
        self,
        banco_teste
    ):
        with pytest.raises(ValueError):
            login_usuario({
                "email": "inexistente@exemplo.com",
                "senha": "Senha123!",
                "tipo": "produtor"
            })

    def test_login_com_tipo_incompativel(
        self,
        banco_teste,
        dados_usuario
    ):
        criar_usuario(dados_usuario)

        with pytest.raises(ValueError):
            login_usuario({
                "email": dados_usuario["email"],
                "senha": dados_usuario["senha"],
                "tipo": "estabelecimento"
            })

import jwt

from datetime import datetime, timedelta, timezone
from fastapi import HTTPException

from auth.security import (
    criar_token,
    SECRET_KEY,
    ALGORITHM
)

from auth.dependencies import get_current_user

class TestValidacaoJWT:

    def test_rejeita_requisicao_sem_token(
        self,
        banco_teste
    ):
        with pytest.raises(HTTPException) as erro:
            get_current_user(access_token=None)

        assert erro.value.status_code == 401

    def test_rejeita_token_invalido(
        self,
        banco_teste
    ):
        with pytest.raises(HTTPException) as erro:
            get_current_user(access_token="token_invalido")

        assert erro.value.status_code == 401

    def test_rejeita_token_expirado(
        self,
        banco_teste
    ):
        payload = {
            "sub": "1",
            "tipo": "produtor",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=5)
        }

        token = jwt.encode(
            payload,
            SECRET_KEY,
            algorithm=ALGORITHM
        )

        with pytest.raises(HTTPException) as erro:
            get_current_user(access_token=token)

        assert erro.value.status_code == 401

    def test_rejeita_token_sem_sub(
        self,
        banco_teste
    ):
        token = jwt.encode(
            {
                "tipo": "produtor",
                "exp": datetime.now(timezone.utc) + timedelta(minutes=10)
            },
            SECRET_KEY,
            algorithm=ALGORITHM
        )

        with pytest.raises(HTTPException) as erro:
            get_current_user(access_token=token)

        assert erro.value.status_code == 401

    def test_rejeita_token_sem_tipo(
        self,
        banco_teste
    ):
        token = jwt.encode(
            {
                "sub": "1",
                "exp": datetime.now(timezone.utc) + timedelta(minutes=10)
            },
            SECRET_KEY,
            algorithm=ALGORITHM
        )

        with pytest.raises(HTTPException) as erro:
            get_current_user(access_token=token)

        assert erro.value.status_code == 401

    def test_rejeita_usuario_inexistente(
        self,
        banco_teste
    ):
        token = criar_token(
            user_id=99999,
            tipo="produtor"
        )

        with pytest.raises(HTTPException) as erro:
            get_current_user(access_token=token)

        assert erro.value.status_code == 401

    def test_aceita_token_valido(
        self,
        banco_teste,
        dados_usuario
    ):
        usuario = criar_usuario(dados_usuario)

        token = criar_token(
            user_id=usuario.id,
            tipo=usuario.tipo
        )

        resultado = get_current_user(
            access_token=token
        )

        assert resultado["user_id"] == usuario.id
        assert resultado["tipo"] == usuario.tipo
        assert resultado["nome"] == usuario.nome


class TestValidacaoJWT:

    def test_rejeita_requisicao_sem_token(
        self,
        banco_teste
    ):
        with pytest.raises(HTTPException) as erro:
            get_current_user(access_token=None)

        assert erro.value.status_code == 401

    def test_rejeita_token_invalido(
        self,
        banco_teste
    ):
        with pytest.raises(HTTPException) as erro:
            get_current_user(access_token="token_invalido")

        assert erro.value.status_code == 401

    def test_rejeita_token_expirado(
        self,
        banco_teste
    ):
        payload = {
            "sub": "1",
            "tipo": "produtor",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=5)
        }

        token = jwt.encode(
            payload,
            SECRET_KEY,
            algorithm=ALGORITHM
        )

        with pytest.raises(HTTPException) as erro:
            get_current_user(access_token=token)

        assert erro.value.status_code == 401

    def test_rejeita_token_sem_sub(
        self,
        banco_teste
    ):
        token = jwt.encode(
            {
                "tipo": "produtor",
                "exp": datetime.now(timezone.utc) + timedelta(minutes=10)
            },
            SECRET_KEY,
            algorithm=ALGORITHM
        )

        with pytest.raises(HTTPException) as erro:
            get_current_user(access_token=token)

        assert erro.value.status_code == 401

    def test_rejeita_token_sem_tipo(
        self,
        banco_teste
    ):
        token = jwt.encode(
            {
                "sub": "1",
                "exp": datetime.now(timezone.utc) + timedelta(minutes=10)
            },
            SECRET_KEY,
            algorithm=ALGORITHM
        )

        with pytest.raises(HTTPException) as erro:
            get_current_user(access_token=token)

        assert erro.value.status_code == 401

    def test_rejeita_usuario_inexistente(
        self,
        banco_teste
    ):
        token = criar_token(
            user_id=99999,
            tipo="produtor"
        )

        with pytest.raises(HTTPException) as erro:
            get_current_user(access_token=token)

        assert erro.value.status_code == 401

    def test_aceita_token_valido(
        self,
        banco_teste,
        dados_usuario
    ):
        usuario = criar_usuario(dados_usuario)

        token = criar_token(
            user_id=usuario.id,
            tipo=usuario.tipo
        )

        resultado = get_current_user(
            access_token=token
        )

        assert resultado["user_id"] == usuario.id
        assert resultado["tipo"] == usuario.tipo
        assert resultado["nome"] == usuario.nome
