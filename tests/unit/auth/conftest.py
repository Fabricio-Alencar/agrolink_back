import os

# Define a chave antes de qualquer importação do projeto.
os.environ["SECRET_KEY"] = "chave_ficticia_para_testes"

import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def db_mock():
    """Simula a sessão do banco de dados."""
    with patch("auth.dependencies.SessionLocal") as session_mock:
        db = MagicMock()
        session_mock.return_value = db

        yield {
            "session": db,
            "session_local": session_mock
        }