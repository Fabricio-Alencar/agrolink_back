import os

# Define configurações seguras antes de importar os módulos do projeto.
# Impede que o banco configurado no .env seja utilizado nesta bateria.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SECRET_KEY"] = "chave-exclusiva-para-testes-agrolink"
os.environ["AZURE_STORAGE_CONNECTION_STRING"] = "UseDevelopmentStorage=true"
os.environ["REDIS_HOST"] = "localhost"
os.environ["REDIS_PASSWORD"] = "senha-ficticia-testes"
import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base
from models.usuario import Usuario
from models.produto import Produto
from models.negociacao import Negociacao

import services.usuario_service as usuario_service
import auth.dependencies as auth_dependencies

import services.produto_service as produto_service
produto_service.upload_arquivo = lambda *args, **kwargs: None
produto_service.deletar_arquivo = lambda *args, **kwargs: None
class RedisFake:
    def delete(self, *args, **kwargs):
        return 1


produto_service.redis_client = RedisFake()
@pytest.fixture
def banco_teste(monkeypatch):
    engine_teste = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )

    TestSessionLocal = sessionmaker(
        bind=engine_teste,
        autoflush=False,
        autocommit=False
    )

    Base.metadata.create_all(bind=engine_teste)

    monkeypatch.setattr(
        usuario_service,
        "SessionLocal",
        TestSessionLocal
    )

    monkeypatch.setattr(
        auth_dependencies,
        "SessionLocal",
        TestSessionLocal
    )
    monkeypatch.setattr(
        produto_service,
        "SessionLocal",
        TestSessionLocal
    )

    yield TestSessionLocal


    Base.metadata.drop_all(bind=engine_teste)
    engine_teste.dispose()
