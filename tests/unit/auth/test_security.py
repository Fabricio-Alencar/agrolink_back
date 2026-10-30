
from datetime import datetime, timedelta, timezone

import jwt
import pytest

import os
import subprocess
import sys


from auth import security


def test_criar_token_sucesso():
    """Verifica se cria um token com os dados e a validade esperados."""

    token = security.criar_token(10, "produtor")

    payload = jwt.decode(
        token,
        security.SECRET_KEY,
        algorithms=[security.ALGORITHM]
    )

    assert payload["sub"] == "10"
    assert payload["tipo"] == "produtor"

    # Verifica se o token possui uma data de expiração.
    assert "exp" in payload

    # Verifica se o token expira aproximadamente em 24 horas.
    agora = datetime.now(timezone.utc).timestamp()
    assert agora < payload["exp"] <= agora + (24 * 60 * 60)


def test_decodificar_token_sucesso():
    """Verifica se decodifica corretamente um token válido."""

    token = security.criar_token(20, "estabelecimento")

    payload = security.decodificar_token(token)

    assert payload["sub"] == "20"
    assert payload["tipo"] == "estabelecimento"


def test_decodificar_token_expirado():
    """Verifica se rejeita um token cuja validade já terminou."""

    payload = {
        "sub": "10",
        "tipo": "produtor",
        "exp": datetime.now(timezone.utc) - timedelta(hours=1)
    }

    token = jwt.encode(
        payload,
        security.SECRET_KEY,
        algorithm=security.ALGORITHM
    )

    with pytest.raises(jwt.ExpiredSignatureError):
        security.decodificar_token(token)


def test_decodificar_token_assinatura_invalida():
    """Verifica se rejeita um token assinado com outra chave."""

    token = jwt.encode(
        {
            "sub": "10",
            "tipo": "produtor"
        },
        "outra_chave_ficticia",
        algorithm=security.ALGORITHM
    )

    with pytest.raises(jwt.InvalidSignatureError):
        security.decodificar_token(token)


def test_decodificar_token_formato_invalido():
    """Verifica se rejeita um token com formato inválido."""

    with pytest.raises(jwt.InvalidTokenError):
        security.decodificar_token("token_invalido")

def test_secret_key_nao_definida(monkeypatch):
    """Verifica se gera erro quando SECRET_KEY não está definida."""

    import importlib
    import auth.security

    monkeypatch.setattr(os, "getenv", lambda chave, *args: None)

    with pytest.raises(
        RuntimeError,
        match="SECRET_KEY não foi definida no .env"
    ):
        importlib.reload(auth.security)  
