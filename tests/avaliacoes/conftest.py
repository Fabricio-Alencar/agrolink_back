"""
Configuração dos testes da funcionalidade de avaliações.

Os testes usam um banco SQLite temporário (separado do banco de produção)
e substituem o Redis e o Azure Blob Storage por versões falsas, para que
nenhum dado de teste chegue ao sistema publicado.
"""
import os
import sys
import tempfile
from pathlib import Path

import pytest

# Variáveis de ambiente de teste (antes de importar a aplicação)
_DB_DIR = tempfile.mkdtemp(prefix="agrolink_testes_")
os.environ["DATABASE_URL"] = f"sqlite:///{_DB_DIR}/teste.db"
os.environ["SECRET_KEY"] = "chave-de-teste"
os.environ["REDIS_HOST"] = "redis-falso"
os.environ["REDIS_PASSWORD"] = "senha-falsa"
os.environ["AZURE_STORAGE_CONNECTION_STRING"] = (
    "DefaultEndpointsProtocol=https;AccountName=teste;"
    "AccountKey=dGVzdGU=;EndpointSuffix=core.windows.net"
)

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


class RedisFalso:
    """Substitui o Redis guardando os dados em memória."""

    def __init__(self):
        self.dados = {}
        self.chaves_apagadas = []

    def get(self, chave):
        return self.dados.get(chave)

    def set(self, chave, valor, ex=None):
        self.dados[chave] = valor

    def delete(self, chave):
        self.chaves_apagadas.append(chave)
        self.dados.pop(chave, None)


@pytest.fixture
def redis_falso(monkeypatch):
    import services.cache_service as cache_service
    import services.avaliacoes_service as avaliacoes_service
    import services.marketplace_service as marketplace_service

    falso = RedisFalso()
    for modulo in (cache_service, avaliacoes_service, marketplace_service):
        monkeypatch.setattr(modulo, "redis_client", falso)

    # Outros serviços que limpam o cache (produtos, perfil)
    for nome in ("services.produto_service", "services.perfil_service"):
        modulo = sys.modules.get(nome)
        if modulo is not None and hasattr(modulo, "redis_client"):
            monkeypatch.setattr(modulo, "redis_client", falso)

    return falso


@pytest.fixture
def banco():
    """Recria as tabelas antes de cada teste (banco limpo)."""
    import main  # noqa: F401  (registra todos os modelos)
    from database import Base, engine
    from chat_database import ChatBase

    Base.metadata.drop_all(bind=engine)
    ChatBase.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    ChatBase.metadata.create_all(bind=engine)
    yield
    engine.dispose()


@pytest.fixture
def app(banco, redis_falso):
    import main
    return main.app


def novo_cliente(app):
    from fastapi.testclient import TestClient
    # https porque o cookie do login é "secure"
    return TestClient(app, base_url="https://testserver")


@pytest.fixture
def cliente(app):
    return novo_cliente(app)


# =========================
# FUNÇÕES DE APOIO
# =========================
def cadastrar_e_logar(app, nome, email, tipo):
    cliente = novo_cliente(app)
    r = cliente.post("/cadastro", json={
        "nome": nome, "email": email, "senha": "Senha@123", "tipo": tipo,
        "telefone": "11999999999", "estado": "SP", "cidade": "São Paulo",
    })
    assert r.status_code == 201, r.text
    usuario_id = r.json()["user"]["id"]

    r = cliente.post("/login", json={"email": email, "senha": "Senha@123", "tipo": tipo})
    assert r.status_code == 200, r.text
    return cliente, usuario_id


def criar_produto(cliente_produtor, nome="Tomate", preco=8.5):
    r = cliente_produtor.post("/produtos", data={
        "nome": nome, "preco": str(preco), "quantidade": "100", "unidade": "kg",
        "categoria": "Legumes", "descricao": "Produto de teste",
        "status_produto": "publicado",
    })
    assert r.status_code == 201, r.text
    return r.json()["produto"]["id"]


def fazer_pedido(cliente_comprador, produto_id):
    r = cliente_comprador.post("/negociar", json={
        "produto_id": produto_id, "quantidade": 10,
        "data_entrega": "2026-12-10", "descricao": "Pedido de teste",
    })
    assert r.status_code == 201, r.text
    return r.json()["id"]


def finalizar_pedido(cliente_produtor, cliente_comprador, negociacao_id):
    r = cliente_produtor.put(f"/negociacoes/{negociacao_id}/status", json={"status": "aceito"})
    assert r.status_code == 200, r.text
    r = cliente_produtor.put(f"/negociacoes/{negociacao_id}/confirmar", json={"acao": "confirmar_entrega"})
    assert r.status_code == 200, r.text
    r = cliente_comprador.put(f"/negociacoes/{negociacao_id}/confirmar", json={"acao": "confirmar_recebimento"})
    assert r.status_code == 200, r.text
    assert r.json()["status_atual"] == "Finalizado"


@pytest.fixture
def cenario(app):
    """Produtor com um produto publicado e um estabelecimento com um pedido finalizado."""
    produtor, produtor_id = cadastrar_e_logar(app, "Joao Produtor", "produtor@teste.com", "produtor")
    comprador, comprador_id = cadastrar_e_logar(app, "Mercado Bom", "mercado@teste.com", "estabelecimento")
    produto_id = criar_produto(produtor)
    negociacao_id = fazer_pedido(comprador, produto_id)
    finalizar_pedido(produtor, comprador, negociacao_id)
    return {
        "app": app, "produtor": produtor, "produtor_id": produtor_id,
        "comprador": comprador, "comprador_id": comprador_id,
        "produto_id": produto_id, "negociacao_id": negociacao_id,
    }
