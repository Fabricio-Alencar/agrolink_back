
import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def db_mock():
    """Simula a sessão do banco de dados."""

    with patch("services.negociacoes_service.SessionLocal") as session_mock:

        db = MagicMock()
        session_mock.return_value = db

        yield {
            "session": db,
            "session_local": session_mock
        }
