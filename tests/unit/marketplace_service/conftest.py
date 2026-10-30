
import sys
import pytest
from unittest.mock import MagicMock

from fakes import ProdutoFake, ProdutorFake


# ======================================
# SIMULAÇÃO DO CACHE SERVICE
# ======================================

# Evita exigir REDIS_HOST e conexão com o Redis.
cache_mock = MagicMock()
cache_mock.invalidar_cache_marketplace = MagicMock()

sys.modules["services.cache_service"] = cache_mock


# ======================================
# FIXTURE DO BANCO DE DADOS
# ======================================

@pytest.fixture
def banco_mock(monkeypatch):
    """Simula a sessão do banco de dados."""
    import services.marketplace_service as service

    banco = MagicMock()
    monkeypatch.setattr(service, "SessionLocal", lambda: banco)

    return banco


# ======================================
# FIXTURES DOS MODELOS
# ======================================

@pytest.fixture
def produto_fake():
    """Cria um produto fictício."""
    return ProdutoFake(
        id=10,
        produtor_id=20
    )


@pytest.fixture
def produtor_fake():
    """Cria um produtor fictício."""
    return ProdutorFake(
        id=20,
        nome="João",
        estado="SP",
        cidade="Itaberá",
        foto_perfil=None
    )
