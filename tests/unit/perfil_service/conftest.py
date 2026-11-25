import pytest

from services import perfil_service

from tests.unit.perfil_service.fakes import (
    FakeDB,
    FakeRedis,
    FakeUsuario
)


@pytest.fixture
def usuario():
    return FakeUsuario()


@pytest.fixture
def db(usuario, monkeypatch):
    banco = FakeDB(usuario=usuario)

    monkeypatch.setattr(
        perfil_service,
        "SessionLocal",
        lambda: banco
    )

    return banco


@pytest.fixture
def redis(monkeypatch):
    cache = FakeRedis()

    monkeypatch.setattr(
        perfil_service,
        "redis_client",
        cache
    )

    return cache