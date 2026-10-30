from services.negociacoes_service import deletar_negociacao_service
from models import Negociacao
import pytest


def test_ocultar_negociacao_como_comprador(db_mock):
    negociacao = Negociacao()
    negociacao.id = 1
    negociacao.comprador_id = 20
    negociacao.vendedor_id = 10
    negociacao.oculto_comprador = False
    negociacao.oculto_vendedor = False

    db_mock["session"].get.return_value = negociacao

    resultado = deletar_negociacao_service(1, 20)

    # Verifica se a negociação foi ocultada para o comprador
    assert negociacao.oculto_comprador is True

    # Verifica se a negociação continua visível para o vendedor
    assert negociacao.oculto_vendedor is False

    # Verifica se a negociação não foi excluída permanentemente
    db_mock["session"].delete.assert_not_called()

    # Verifica se a transação foi confirmada
    db_mock["session"].commit.assert_called_once()

    # Verifica se o retorno indica que a negociação foi ocultada
    assert resultado == ({"mensagem": "Negociação ocultada da sua tela."}, 200)

    # Resultado esperado: negociação ocultada apenas para o comprador.


def test_ocultar_negociacao_como_vendedor(db_mock):
    negociacao = Negociacao()
    negociacao.id = 1
    negociacao.comprador_id = 20
    negociacao.vendedor_id = 10
    negociacao.oculto_comprador = False
    negociacao.oculto_vendedor = False

    db_mock["session"].get.return_value = negociacao

    resultado = deletar_negociacao_service(1, 10)

    # Verifica se a negociação foi ocultada para o vendedor
    assert negociacao.oculto_vendedor is True

    # Verifica se a negociação continua visível para o comprador
    assert negociacao.oculto_comprador is False

    # Verifica se a negociação não foi excluída permanentemente
    db_mock["session"].delete.assert_not_called()

    # Verifica se a transação foi confirmada
    db_mock["session"].commit.assert_called_once()

    # Resultado esperado: negociação ocultada apenas para o vendedor.


def test_excluir_negociacao_permanentemente(db_mock):
    negociacao = Negociacao()
    negociacao.id = 1
    negociacao.comprador_id = 20
    negociacao.vendedor_id = 10
    negociacao.oculto_comprador = False
    negociacao.oculto_vendedor = True

    db_mock["session"].get.return_value = negociacao

    resultado = deletar_negociacao_service(1, 20)

    # Verifica se a negociação foi ocultada para o comprador
    assert negociacao.oculto_comprador is True

    # Verifica se a negociação foi excluída permanentemente
    db_mock["session"].delete.assert_called_once_with(negociacao)

    # Verifica se a transação foi confirmada
    db_mock["session"].commit.assert_called_once()

    # Verifica se o retorno indica exclusão permanente
    assert resultado == ({"mensagem": "Negociação excluída permanentemente do banco de dados."}, 200)

    # Resultado esperado: negociação excluída quando ambos os participantes a ocultaram.


def test_deletar_negociacao_inexistente(db_mock):
    db_mock["session"].get.return_value = None

    resultado = deletar_negociacao_service(999, 20)

    # Verifica se o retorno indica negociação inexistente
    assert resultado == ({"erro": "Negociação não encontrada"}, 404)

    # Verifica se a negociação não foi excluída
    db_mock["session"].delete.assert_not_called()

    # Verifica se a transação não foi confirmada
    db_mock["session"].commit.assert_not_called()

    # Resultado esperado: erro 404 quando a negociação não existe.


def test_deletar_negociacao_sem_permissao(db_mock):
    negociacao = Negociacao()
    negociacao.id = 1
    negociacao.comprador_id = 20
    negociacao.vendedor_id = 10
    negociacao.oculto_comprador = False
    negociacao.oculto_vendedor = False

    db_mock["session"].get.return_value = negociacao

    resultado = deletar_negociacao_service(1, 99)

    # Verifica se o retorno indica acesso negado
    assert resultado == ({"erro": "Acesso negado"}, 403)

    # Verifica se nenhum participante foi alterado
    assert negociacao.oculto_comprador is False
    assert negociacao.oculto_vendedor is False

    # Verifica se a negociação não foi excluída
    db_mock["session"].delete.assert_not_called()

    # Verifica se a transação não foi confirmada
    db_mock["session"].commit.assert_not_called()

    # Resultado esperado: usuário que não participa da negociação recebe erro 403.

def test_deletar_negociacao_erro_no_commit(db_mock):
    negociacao = Negociacao()
    negociacao.id = 1
    negociacao.comprador_id = 20
    negociacao.vendedor_id = 10
    negociacao.oculto_comprador = False
    negociacao.oculto_vendedor = False

    db_mock["session"].get.return_value = negociacao

    # Simula uma falha durante a confirmação da transação
    db_mock["session"].commit.side_effect = Exception("Erro no banco de dados")

    with pytest.raises(Exception, match="Erro no banco de dados"):
        deletar_negociacao_service(1, 20)

    # Verifica se o rollback foi executado
    db_mock["session"].rollback.assert_called_once()

    # Verifica se a sessão foi fechada
    db_mock["session"].close.assert_called_once()

    # Resultado esperado: a transação é revertida e a exceção é propagada.    
