
import pytest
from datetime import date

import services.marketplace_service as service


# ======================================
# TESTE DE REGISTRO COM SUCESSO
# ======================================

def test_registrar_pedido_sucesso(banco_mock, produto_fake):
    banco_mock.get.return_value = produto_fake

    dados = {
        "produto_id": 10,
        "quantidade": "5",
        "data_entrega": "2026-11-10",
        "descricao": "Entrega pela manhã"
    }

    resultado = service.registrar_pedido(5, dados)

    banco_mock.get.assert_called_once_with(service.Produto, 10)
    banco_mock.add.assert_called_once()
    banco_mock.commit.assert_called_once()
    banco_mock.refresh.assert_called_once_with(resultado)

    assert resultado.produto_id == 10
    assert resultado.vendedor_id == 20
    assert resultado.comprador_id == 5
    assert resultado.quantidade == 5.0
    assert resultado.data_entrega == date(2026, 11, 10)
    assert resultado.descricao == "Entrega pela manhã"
    assert resultado.status == "pendente"

    banco_mock.close.assert_called_once()


# ======================================
# TESTE DE PRODUTO INEXISTENTE
# ======================================

def test_registrar_pedido_produto_inexistente(banco_mock):
    banco_mock.get.return_value = None

    dados = {
        "produto_id": 99,
        "quantidade": "5",
        "data_entrega": "2026-11-10"
    }

    with pytest.raises(Exception, match="Produto não encontrado."):
        service.registrar_pedido(5, dados)

    banco_mock.add.assert_not_called()
    banco_mock.commit.assert_not_called()
    banco_mock.rollback.assert_called_once()
    banco_mock.close.assert_called_once()


# ======================================
# TESTE DE DATA INVÁLIDA
# ======================================

def test_registrar_pedido_data_invalida(banco_mock, produto_fake):
    banco_mock.get.return_value = produto_fake

    dados = {
        "produto_id": 10,
        "quantidade": "5",
        "data_entrega": "data-invalida"
    }

    resultado = service.registrar_pedido(5, dados)

    assert resultado.data_entrega is None
    banco_mock.commit.assert_called_once()
    banco_mock.close.assert_called_once()


# ======================================
# TESTE SEM DATA DE ENTREGA
# ======================================

def test_registrar_pedido_sem_data_entrega(banco_mock, produto_fake):
    banco_mock.get.return_value = produto_fake

    dados = {
        "produto_id": 10,
        "quantidade": "5"
    }

    resultado = service.registrar_pedido(5, dados)

    assert resultado.data_entrega is None
    banco_mock.commit.assert_called_once()
    banco_mock.close.assert_called_once()


# ======================================
# TESTE DE ERRO NO COMMIT
# ======================================

def test_registrar_pedido_erro_no_commit(banco_mock, produto_fake):
    banco_mock.get.return_value = produto_fake
    banco_mock.commit.side_effect = Exception("Erro no banco")

    dados = {
        "produto_id": 10,
        "quantidade": "5",
        "data_entrega": "2026-11-10"
    }

    with pytest.raises(Exception, match="Erro no banco"):
        service.registrar_pedido(5, dados)

    banco_mock.rollback.assert_called_once()
    banco_mock.close.assert_called_once()
