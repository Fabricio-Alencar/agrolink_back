import pytest
from unittest.mock import MagicMock

import services.produto_service as service
from services import cache_service
from tests.unit.produto_service.fakes import UsuarioFake, ProdutoFake


def dados_produto(**alteracoes):
    dados = {
        "nome": "Tomate",
        "preco": 5.0,
        "produtor_id": 10,
        "quantidade": 20,
        "status": "publicado",
        "categoria": "Frutas",
        "unidade": "kg",
        "descricao": "Tomate fresco",
    }
    return {**dados, **alteracoes}


def configurar_produtor(db):
    db.get.return_value = UsuarioFake(id=10, tipo="produtor")


def simular_produto(monkeypatch):
    produtos_criados = []

    def criar_produto_fake(**dados):
        produto = ProdutoFake(id=1, **dados)
        produtos_criados.append(produto)
        return produto

    monkeypatch.setattr(service, "Produto", criar_produto_fake)
    return produtos_criados


def test_criar_produto_com_sucesso_sem_foto(banco_mock, monkeypatch):
    db = banco_mock
    configurar_produtor(db)
    produtos_criados = simular_produto(monkeypatch)

    monkeypatch.setattr(
        service, "invalidar_cache_marketplace", lambda: None
    )

    resultado = service.criar_produto(
        dados_produto(), arquivo_foto=None
    )

    assert resultado == produtos_criados[0]
    assert resultado.foto == "foto_generica.png"
    db.get.assert_called_once_with(service.Usuario, 10)
    db.add.assert_called_once_with(resultado)
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(resultado)
    db.close.assert_called_once()


def test_criar_produto_com_sucesso_com_foto(banco_mock, monkeypatch):
    db = banco_mock
    configurar_produtor(db)

    arquivo = MagicMock()
    arquivo.filename = "foto.png"

    upload_mock = MagicMock()
    monkeypatch.setattr(service, "upload_arquivo", upload_mock)
    monkeypatch.setattr(service, "invalidar_cache_marketplace", lambda: None)
    simular_produto(monkeypatch)

    resultado = service.criar_produto(dados_produto(), arquivo_foto=arquivo)

    assert resultado.nome == "Tomate"
    assert resultado.produtor_id == 10
    assert resultado.foto.endswith(".png")

    db.add.assert_called_once_with(resultado)
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(resultado)
    db.close.assert_called_once()

    upload_mock.assert_called_once_with(
        arquivo.file, resultado.foto, service.CONTAINER_PRODUTOS
    )


def test_criar_produto_usuario_nao_encontrado(banco_mock):
    banco_mock.get.return_value = None

    with pytest.raises(Exception, match="Usuário não encontrado"):
        service.criar_produto(dados_produto(), arquivo_foto=None)

    banco_mock.close.assert_called_once()


def test_criar_produto_usuario_nao_produtor(banco_mock):
    banco_mock.get.return_value = UsuarioFake(id=10, tipo="estabelecimento")

    with pytest.raises(Exception, match="Apenas produtores podem criar produtos"):
        service.criar_produto(dados_produto(), arquivo_foto=None)

    banco_mock.close.assert_called_once()


def test_criar_produto_erro_ao_salvar_no_banco(banco_mock, monkeypatch):
    db = banco_mock
    configurar_produtor(db)
    simular_produto(monkeypatch)

    db.commit.side_effect = Exception("Erro de conexão")

    with pytest.raises(Exception, match="Erro ao salvar no banco"):
        service.criar_produto(dados_produto(), arquivo_foto=None)

    db.rollback.assert_called_once()
    db.close.assert_called_once()


def test_criar_produto_falha_ao_limpar_redis(banco_mock, monkeypatch):
    db = banco_mock
    configurar_produtor(db)
    simular_produto(monkeypatch)

    def erro_redis(chave):
        raise Exception("Redis indisponível")

    monkeypatch.setattr(
        cache_service.redis_client, "delete", erro_redis
    )

    resultado = service.criar_produto(
        dados_produto(), arquivo_foto=None
    )

    assert resultado.nome == "Tomate"
    assert resultado.produtor_id == 10
    assert resultado.foto == "foto_generica.png"

    db.add.assert_called_once_with(resultado)
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(resultado)
    db.close.assert_called_once()


def test_criar_produto_remove_foto_azure_se_banco_falhar(banco_mock, monkeypatch):
    db = banco_mock
    configurar_produtor(db)

    arquivo = MagicMock()
    arquivo.filename = "tomate.png"

    upload_mock = MagicMock()
    deletar_mock = MagicMock()

    monkeypatch.setattr(service, "upload_arquivo", upload_mock)
    monkeypatch.setattr(service, "deletar_arquivo", deletar_mock)
    simular_produto(monkeypatch)

    db.commit.side_effect = Exception("Erro de conexão")

    with pytest.raises(Exception, match="Erro ao salvar no banco"):
        service.criar_produto(dados_produto(), arquivo_foto=arquivo)

    upload_mock.assert_called_once()

    nome_blob = upload_mock.call_args.args[1]
    deletar_mock.assert_called_once_with(
        nome_blob, service.CONTAINER_PRODUTOS
    )

    db.rollback.assert_called_once()
    db.close.assert_called_once()
