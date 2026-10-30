from services.negociacoes_service import registrar_confirmacao_service
from models import Negociacao
import pytest



def test_confirmar_entrega_com_sucesso(db_mock):
    negociacao = Negociacao()
    negociacao.id = 1
    negociacao.vendedor_id = 10
    negociacao.comprador_id = 20
    negociacao.status = "aceito"
    negociacao.entrega_confirmada = False
    negociacao.recebimento_confirmado = False

    db_mock["session"].get.return_value = negociacao

    resultado = registrar_confirmacao_service(1, "confirmar_entrega", 10)

    # Verifica se a entrega foi confirmada
    assert negociacao.entrega_confirmada is True

    # Verifica se o status foi atualizado
    assert negociacao.status == "Entregue"

    # Verifica se a transação foi confirmada
    db_mock["session"].commit.assert_called_once()

    # Verifica se o retorno indica sucesso
    assert resultado == ({"mensagem": "Confirmação registrada com sucesso","status_atual": "Entregue"}, 200)

    # Resultado esperado: produtor confirma a entrega e o pedido fica Entregue.


def test_confirmar_recebimento_com_sucesso(db_mock):
    negociacao = Negociacao()
    negociacao.id = 1
    negociacao.vendedor_id = 10
    negociacao.comprador_id = 20
    negociacao.status = "entregue"
    negociacao.entrega_confirmada = True
    negociacao.recebimento_confirmado = False

    db_mock["session"].get.return_value = negociacao

    resultado = registrar_confirmacao_service(1, "confirmar_recebimento", 20)

    # Verifica se o recebimento foi confirmado
    assert negociacao.recebimento_confirmado is True

    # Verifica se a entrega permanece confirmada
    assert negociacao.entrega_confirmada is True

    # Verifica se o pedido foi finalizado
    assert negociacao.status == "Finalizado"

    # Verifica se a transação foi confirmada
    db_mock["session"].commit.assert_called_once()

    # Verifica se o retorno indica sucesso
    assert resultado == ({
        "mensagem": "Confirmação registrada com sucesso",
        "status_atual": "Finalizado"
    }, 200)

    # Resultado esperado: recebimento confirmado finaliza o pedido quando a entrega já foi confirmada.


def test_confirmar_recebimento_sem_entrega_anterior(db_mock):
    negociacao = Negociacao()
    negociacao.id = 1
    negociacao.vendedor_id = 10
    negociacao.comprador_id = 20
    negociacao.status = "aceito"
    negociacao.entrega_confirmada = False
    negociacao.recebimento_confirmado = False

    db_mock["session"].get.return_value = negociacao

    resultado = registrar_confirmacao_service(1, "confirmar_recebimento", 20)

    # Verifica se o recebimento foi confirmado
    assert negociacao.recebimento_confirmado is True

    # Verifica se a entrega também foi marcada como confirmada
    assert negociacao.entrega_confirmada is True

    # Verifica se o pedido foi finalizado
    assert negociacao.status == "Finalizado"

    # Verifica se a transação foi confirmada
    db_mock["session"].commit.assert_called_once()

    # Resultado esperado: confirmação de recebimento também confirma a entrega e finaliza o pedido.
    # Mesmo sem o produtor confirmar o recebimento, já é tido como finalizado

def test_confirmar_negociacao_inexistente(db_mock):
    db_mock["session"].get.return_value = None

    resultado = registrar_confirmacao_service(999, "confirmar_entrega", 10)

    # Verifica se o retorno indica negociação inexistente
    assert resultado == ({"erro": "Negociação não encontrada"}, 404)

    # Verifica se a transação não foi confirmada
    db_mock["session"].commit.assert_not_called()

    # Verifica se a sessão foi fechada
    db_mock["session"].close.assert_called_once()

    # Resultado esperado: erro 404 quando a negociação não existe.


def test_confirmar_negociacao_com_status_invalido(db_mock):
    negociacao = Negociacao()
    negociacao.vendedor_id = 10
    negociacao.comprador_id = 20
    negociacao.status = "pendente"

    db_mock["session"].get.return_value = negociacao

    resultado = registrar_confirmacao_service(1, "confirmar_entrega", 10)

    # Verifica se o retorno indica status inválido
    assert resultado == ({"erro": "Não é possível confirmar um pedido pendente."}, 400)

    # Verifica se a transação não foi confirmada
    db_mock["session"].commit.assert_not_called()

    # Resultado esperado: não é possível confirmar pedido pendente.


def test_confirmar_entrega_por_usuario_sem_permissao(db_mock):
    negociacao = Negociacao()
    negociacao.vendedor_id = 10
    negociacao.comprador_id = 20
    negociacao.status = "aceito"

    db_mock["session"].get.return_value = negociacao

    resultado = registrar_confirmacao_service(1, "confirmar_entrega", 20)

    # Verifica se o retorno indica falta de permissão
    assert resultado == ({"erro": "Apenas o produtor pode confirmar a entrega"}, 403)

    # Verifica se a transação não foi confirmada
    db_mock["session"].commit.assert_not_called()

    # Resultado esperado: somente o produtor pode confirmar a entrega.


def test_confirmar_recebimento_por_usuario_sem_permissao(db_mock):
    negociacao = Negociacao()
    negociacao.vendedor_id = 10
    negociacao.comprador_id = 20
    negociacao.status = "aceito"

    db_mock["session"].get.return_value = negociacao

    resultado = registrar_confirmacao_service(1, "confirmar_recebimento", 10)

    # Verifica se o retorno indica falta de permissão
    assert resultado == ({"erro": "Apenas o estabelecimento pode confirmar o recebimento"}, 403)

    # Verifica se a transação não foi confirmada
    db_mock["session"].commit.assert_not_called()

    # Resultado esperado: somente o estabelecimento pode confirmar o recebimento.


def test_confirmar_com_acao_invalida(db_mock):
    negociacao = Negociacao()
    negociacao.vendedor_id = 10
    negociacao.comprador_id = 20
    negociacao.status = "aceito"
    negociacao.entrega_confirmada = False
    negociacao.recebimento_confirmado = False

    db_mock["session"].get.return_value = negociacao

    resultado = registrar_confirmacao_service(1, "acao_invalida", 10)

    # Verifica se o retorno indica ação inválida
    assert resultado == ({"erro": "Ação inválida"}, 400)

    # Verifica se a transação não foi confirmada
    db_mock["session"].commit.assert_not_called()

    # Resultado esperado: ações diferentes das permitidas retornam erro 400.

def test_registrar_confirmacao_erro_no_commit(db_mock):
    negociacao = Negociacao()
    negociacao.id = 1
    negociacao.vendedor_id = 10
    negociacao.comprador_id = 20
    negociacao.status = "aceito"
    negociacao.entrega_confirmada = False
    negociacao.recebimento_confirmado = False

    db_mock["session"].get.return_value = negociacao

    # Simula uma falha durante a confirmação da transação
    db_mock["session"].commit.side_effect = Exception("Erro no banco de dados")

    with pytest.raises(Exception, match="Erro no banco de dados"):
        registrar_confirmacao_service(1, "confirmar_entrega", 10)

    # Verifica se o rollback foi executado
    db_mock["session"].rollback.assert_called_once()

    # Verifica se a sessão foi fechada
    db_mock["session"].close.assert_called_once()

    # Resultado esperado: a transação é revertida e a exceção é propagada.
