import pytest
from unittest.mock import MagicMock


@pytest.fixture
def banco_mock():
    """Simula a sessão do banco principal."""
    return MagicMock()


@pytest.fixture
def banco_chat_mock():
    """Simula a sessão do banco de chat."""
    return MagicMock()