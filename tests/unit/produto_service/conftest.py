import os
from unittest.mock import MagicMock

import pytest

# Define as variáveis antes de importar o serviço.
os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("REDIS_PASSWORD", "senha_teste")
os.environ.setdefault("REDIS_PORT", "6379")

import services.produto_service as service


@pytest.fixture
def banco_mock(monkeypatch):
    # Cria uma sessão falsa do banco de dados.
    db = MagicMock()

    # Substitui a sessão real pela sessão simulada.
    monkeypatch.setattr(service, "SessionLocal", lambda: db)

    return db