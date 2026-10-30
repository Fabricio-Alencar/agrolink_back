import pytest
from unittest.mock import MagicMock

import services.produto_service as service
from tests.unit.produto_service.fakes import ProdutoFake


def configurar_produto(db, foto="foto_generica.png"):
    produto = ProdutoFake(
        id=1, nome="Tomate", produtor_id=10, foto=foto,
        preco=4.50, quantidade=10, unidade="kg",
        categoria="Legumes", descricao="Tomate fresco",
        status="publicado"
    )
    db.get.return_value = produto
    return produto

# Cria um arquivo fictício para simular o envio de uma foto nos testes
def configurar_foto(nome="tomate.jpg"):
    arquivo = MagicMock()
    arquivo.filename = nome
    arquivo.file = MagicMock()
    return arquivo


# Dados para atualização
data = {
    "nome": "Tomate Italiano",
    "preco": 5.50,
    "quantidade": 20,
    "unidade": "kg",
    "categoria": "Legumes",
    "descricao": "Tomate fresco",
    "status": "publicado"
}


def test_atualizar_produto_com_sucesso_sem_foto(banco_mock, monkeypatch):
    db = banco_mock
    produto = configurar_produto(db)

    monkeypatch.setattr(service, "invalidar_cache_marketplace", lambda: None)

    resultado = service.atualizar_produto(1, 10, data, None)

    assert resultado == produto  # Verifica se o produto foi retornado
    assert all(getattr(produto, campo) == valor for campo, valor in data.items())  # Verifica os campos atualizados

    db.commit.assert_called_once()  # Verifica se as alterações foram salvas
    db.refresh.assert_called_once_with(produto)  # Verifica se o produto foi atualizado
    db.close.assert_called_once()  # Verifica se a sessão foi fechada


def test_atualizar_produto_com_sucesso_com_foto(banco_mock, monkeypatch):
    db = banco_mock
    produto = configurar_produto(db, "foto_antiga.png")
    arquivo = configurar_foto()

    upload = MagicMock()
    deletar = MagicMock()

    monkeypatch.setattr(service, "upload_arquivo", upload)
    monkeypatch.setattr(service, "deletar_arquivo", deletar)
    monkeypatch.setattr(service, "invalidar_cache_marketplace", lambda: None)

    resultado = service.atualizar_produto(1, 10, data, arquivo)
    nome = upload.call_args.args[1]

    assert resultado == produto  # Verifica se o produto foi retornado
    assert all(getattr(produto, campo) == valor for campo, valor in data.items())  # Verifica os campos atualizados
    assert nome.endswith(".jpg") and len(nome.split(".")[0]) == 32  # Verifica extensão e UUID
    assert produto.foto == nome  # Verifica se a foto foi atualizada

    upload.assert_called_once_with(arquivo.file, nome, service.CONTAINER_PRODUTOS)  # Verifica o upload
    deletar.assert_called_once_with("foto_antiga.png", service.CONTAINER_PRODUTOS)  # Verifica a exclusão da foto antiga

    db.commit.assert_called_once()
    db.close.assert_called_once()


def test_atualizar_produto_com_id_incorreto(banco_mock):
    db = banco_mock
    db.get.return_value = None

    with pytest.raises(Exception, match="Produto não encontrado"):
        service.atualizar_produto(999, 10, data, None)

    db.get.assert_called_once_with(service.Produto, 999)  # Verifica a busca pelo ID
    db.commit.assert_not_called()  # Garante que nada foi salvo
    db.close.assert_called_once()  # Verifica o fechamento da sessão


def test_atualizar_produto_com_produtor_nao_permitido(banco_mock):
    db = banco_mock
    configurar_produto(db)

    with pytest.raises(Exception, match="Você não tem permissão para editar este produto"):
        service.atualizar_produto(1, 20, data, None)

    db.commit.assert_not_called()  # Garante que nada foi salvo
    db.close.assert_called_once()  # Verifica o fechamento da sessão


def test_atualizar_produto_com_foto_sem_extensao(banco_mock, monkeypatch):
    db = banco_mock
    produto = configurar_produto(db)
    arquivo = configurar_foto("tomate")

    upload = MagicMock()
    monkeypatch.setattr(service, "upload_arquivo", upload)
    monkeypatch.setattr(service, "invalidar_cache_marketplace", lambda: None)

    service.atualizar_produto(1, 10, data, arquivo)
    nome = upload.call_args.args[1]

    assert "." not in nome  # Verifica se o nome foi gerado sem extensão
    upload.assert_called_once()  # Verifica se o upload foi realizado
    assert produto.foto == nome  # Verifica a atualização da foto


def test_atualizar_produto_com_foto_antiga_generica(banco_mock, monkeypatch):
    db = banco_mock
    configurar_produto(db)
    arquivo = configurar_foto()

    deletar = MagicMock()
    monkeypatch.setattr(service, "upload_arquivo", MagicMock())
    monkeypatch.setattr(service, "deletar_arquivo", deletar)
    monkeypatch.setattr(service, "invalidar_cache_marketplace", lambda: None)

    service.atualizar_produto(1, 10, data, arquivo)

    deletar.assert_not_called()  # Garante que a foto genérica não foi excluída


def test_atualizar_produto_com_erro_ao_excluir_foto_antiga(banco_mock, monkeypatch):
    db = banco_mock
    configurar_produto(db, "foto_antiga.png")
    arquivo = configurar_foto()

    deletar = MagicMock(side_effect=Exception("Erro simulado no Azure"))

    monkeypatch.setattr(service, "upload_arquivo", MagicMock())
    monkeypatch.setattr(service, "deletar_arquivo", deletar)
    monkeypatch.setattr(service, "invalidar_cache_marketplace", lambda: None)

    resultado = service.atualizar_produto(1, 10, data, arquivo)

    assert resultado.foto.endswith(".jpg")  # Verifica se a atualização ocorreu mesmo com erro no Azure
    deletar.assert_called_once()  # Verifica se a exclusão foi tentada


def test_atualizar_produto_com_erro_no_commit(banco_mock, monkeypatch):
    db = banco_mock
    configurar_produto(db)
    arquivo = configurar_foto()

    upload = MagicMock()
    deletar = MagicMock()

    monkeypatch.setattr(service, "upload_arquivo", upload)
    monkeypatch.setattr(service, "deletar_arquivo", deletar)

    db.commit.side_effect = Exception("Erro simulado no banco")

    with pytest.raises(Exception, match="Erro ao atualizar banco"):
        service.atualizar_produto(1, 10, data, arquivo)

    deletar.assert_called_once_with(upload.call_args.args[1], service.CONTAINER_PRODUTOS)  # Verifica a exclusão da nova foto após falha no banco
    db.rollback.assert_called_once()  # Verifica o rollback
    db.close.assert_called_once()  # Verifica o fechamento da sessão