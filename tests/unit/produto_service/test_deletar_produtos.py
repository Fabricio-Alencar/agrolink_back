
import pytest
from unittest.mock import MagicMock

import services.produto_service as service
from tests.unit.produto_service.fakes import ProdutoFake


def configurar_produto(db, foto="foto_generica.png"):
    produto = ProdutoFake(
        id=1,
        nome="Tomate",
        produtor_id=10,
        foto=foto
    )
    db.get.return_value = produto
    return produto


def test_deletar_produto_com_sucesso_foto_generica(banco_mock, monkeypatch):
    db = banco_mock
    produto = configurar_produto(db)

    monkeypatch.setattr(service, "invalidar_cache_marketplace", lambda: None)

    resultado = service.deletar_produto(produto_id=1, user_id=10)

    assert resultado is True
    db.get.assert_called_once_with(service.Produto, 1)
    db.delete.assert_called_once_with(produto)
    db.commit.assert_called_once()
    db.close.assert_called_once()


def test_deletar_produto_com_sucesso_foto_unica(banco_mock, monkeypatch):
    db = banco_mock
    produto = configurar_produto(db, "foto.png")

    # Simula a exclusão da foto no Azure
    deletar_foto_mock = MagicMock()
    monkeypatch.setattr(service, "deletar_arquivo", deletar_foto_mock)

    # Simula a invalidação do cache
    monkeypatch.setattr(service, "invalidar_cache_marketplace", lambda: None)

    resultado = service.deletar_produto(produto_id=1, user_id=10)

    assert resultado is True
    db.get.assert_called_once_with(service.Produto, 1)
    deletar_foto_mock.assert_called_once_with("foto.png", service.CONTAINER_PRODUTOS)
    db.delete.assert_called_once_with(produto)
    db.commit.assert_called_once()
    db.close.assert_called_once()


def test_deletar_produto_com_sucesso_foto_unica_nao_encontrada(banco_mock, monkeypatch):
    db = banco_mock
    produto = configurar_produto(db, "foto.png")

    # Simula uma falha ao excluir a foto no Azure
    deletar_foto_mock = MagicMock(
        side_effect=Exception("Arquivo não encontrado no Azure")
    )
    monkeypatch.setattr(service, "deletar_arquivo", deletar_foto_mock)

    # Simula a invalidação do cache
    monkeypatch.setattr(service, "invalidar_cache_marketplace", lambda: None)

    resultado = service.deletar_produto(produto_id=1, user_id=10)

    assert resultado is True
    db.get.assert_called_once_with(service.Produto, 1)
    deletar_foto_mock.assert_called_once_with("foto.png", service.CONTAINER_PRODUTOS)
    db.delete.assert_called_once_with(produto)
    db.commit.assert_called_once()
    db.close.assert_called_once()


def test_deletar_produto_com_id_incorreto(banco_mock, monkeypatch):
    db = banco_mock
    db.get.return_value = None

    with pytest.raises(Exception, match="Produto não encontrado"):
        service.deletar_produto(produto_id=999, user_id=10)

    # Garante que o produto foi procurado no banco com o id indicado
    db.get.assert_called_once_with(service.Produto, 999)
    db.delete.assert_not_called()
    db.commit.assert_not_called()
    db.close.assert_called_once()


def test_deletar_produto_com_produtor_nao_permitido(banco_mock, monkeypatch):
    db = banco_mock
    configurar_produto(db)

    with pytest.raises(Exception, match="Você não tem permissão para excluir este produto"):
        service.deletar_produto(produto_id=1, user_id=20)

    db.get.assert_called_once_with(service.Produto, 1)
    db.delete.assert_not_called()
    db.commit.assert_not_called()
    db.close.assert_called_once()


def test_deletar_produto_erro_ao_excluir_no_banco(banco_mock, monkeypatch):
    db = banco_mock
    produto = configurar_produto(db)

    # Simula erro ao excluir o produto
    db.delete.side_effect = Exception("Erro simulado no banco")

    # Simula a invalidação do cache
    invalidar_cache_mock = MagicMock()
    monkeypatch.setattr(service, "invalidar_cache_marketplace", invalidar_cache_mock)

    with pytest.raises(Exception, match="Erro ao excluir no banco de dados"):
        service.deletar_produto(produto_id=1, user_id=10)

    db.get.assert_called_once_with(service.Produto, 1)
    db.delete.assert_called_once_with(produto)
    db.commit.assert_not_called()
    db.rollback.assert_called_once()
    db.close.assert_called_once()

    invalidar_cache_mock.assert_not_called()
