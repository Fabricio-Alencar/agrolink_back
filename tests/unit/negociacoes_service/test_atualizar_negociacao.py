from services.negociacoes_service import atualizar_status_negociacao
from models import Negociacao
import pytest



def test_atualizar_status_negociacao_com_sucesso(db_mock):
    negociacao = Negociacao()
    negociacao.id = 1
    negociacao.vendedor_id = 10
    negociacao.comprador_id = 20
    negociacao.status = "pendente"

    db_mock["session"].get.return_value = negociacao

    resultado = atualizar_status_negociacao(1, "aceito", 10)

    # Verifica se a negociação foi consultada
    db_mock["session"].get.assert_called_once_with(Negociacao, 1)

    # Verifica se o status foi atualizado
    assert negociacao.status == "Aceito"

    # Verifica se a data de atualização foi preenchida
    assert negociacao.data_atualizacao is not None

    # Verifica se a transação foi confirmada
    db_mock["session"].commit.assert_called_once()

    # Verifica se o retorno indica sucesso
    assert resultado == ({"mensagem": "Status atualizado para Aceito"}, 200)

    # Verifica se a sessão foi fechada
    db_mock["session"].close.assert_called_once()

    # Resultado esperado: produtor atualiza o pedido pendente para Aceito.


def test_atualizar_status_negociacao_inexistente(db_mock):
    db_mock["session"].get.return_value = None

    resultado = atualizar_status_negociacao(999, "aceito", 10)

    # Verifica se a negociação foi consultada
    db_mock["session"].get.assert_called_once_with(Negociacao, 999)

    # Verifica se a transação não foi confirmada
    db_mock["session"].commit.assert_not_called()

    # Verifica se o retorno contém o erro esperado
    assert resultado == ({"erro": "Negociação não encontrada"}, 404)

    # Verifica se a sessão foi fechada
    db_mock["session"].close.assert_called_once()

    # Resultado esperado: erro 404 quando a negociação não existe.

def test_atualizar_status_usuario_sem_acesso(db_mock):
    negociacao = Negociacao()
    negociacao.vendedor_id = 10
    negociacao.comprador_id = 20
    negociacao.status = "pendente"

    db_mock["session"].get.return_value = negociacao

    resultado = atualizar_status_negociacao(1, "aceito", 99)

    # Verifica se o retorno indica falta de permissão
    assert resultado == ({"erro": "Você não possui acesso a esta negociação."}, 403)

    # Verifica se nenhuma alteração foi confirmada
    db_mock["session"].commit.assert_not_called()

    # Resultado esperado: usuário sem acesso recebe erro 403.


def test_atualizar_status_estabelecimento_tenta_aceitar(db_mock):
    negociacao = Negociacao()
    negociacao.vendedor_id = 10
    negociacao.comprador_id = 20
    negociacao.status = "pendente"

    db_mock["session"].get.return_value = negociacao

    resultado = atualizar_status_negociacao(1, "aceito", 20)

    # Verifica se a operação foi recusada
    assert resultado[1] == 400

    # Verifica se o status permanece inalterado
    assert negociacao.status == "pendente"

    # Verifica se a transação não foi confirmada
    db_mock["session"].commit.assert_not_called()

    # Resultado esperado: estabelecimento não pode aceitar o próprio pedido.


def test_atualizar_status_produtor_recusa_pedido(db_mock):
    negociacao = Negociacao()
    negociacao.vendedor_id = 10
    negociacao.comprador_id = 20
    negociacao.status = "pendente"

    db_mock["session"].get.return_value = negociacao

    resultado = atualizar_status_negociacao(1, "recusado", 10)

    # Verifica se o status foi atualizado
    assert negociacao.status == "Recusado"

    # Verifica se o retorno indica sucesso
    assert resultado[1] == 200

    # Verifica se a transação foi confirmada
    db_mock["session"].commit.assert_called_once()

    # Resultado esperado: produtor pode recusar pedido pendente.


def test_atualizar_status_estabelecimento_cancela_pedido_pendente(db_mock):
    negociacao = Negociacao()
    negociacao.vendedor_id = 10
    negociacao.comprador_id = 20
    negociacao.status = "pendente"

    db_mock["session"].get.return_value = negociacao

    resultado = atualizar_status_negociacao(1, "cancelado", 20)

    # Verifica se o status foi atualizado
    assert negociacao.status == "Cancelado"

    # Verifica se o retorno indica sucesso
    assert resultado[1] == 200

    # Resultado esperado: estabelecimento pode cancelar pedido pendente.


def test_atualizar_status_produtor_tenta_cancelar_pedido_pendente(db_mock):
    negociacao = Negociacao()
    negociacao.vendedor_id = 10
    negociacao.comprador_id = 20
    negociacao.status = "pendente"

    db_mock["session"].get.return_value = negociacao

    resultado = atualizar_status_negociacao(1, "cancelado", 10)

    # Verifica se a operação foi recusada
    assert resultado[1] == 400

    # Verifica se o status permanece inalterado
    assert negociacao.status == "pendente"

    # Resultado esperado: produtor não pode cancelar pedido pendente.


def test_atualizar_status_comprador_cancela_pedido_aceito(db_mock):
    negociacao = Negociacao()
    negociacao.vendedor_id = 10
    negociacao.comprador_id = 20
    negociacao.status = "aceito"

    db_mock["session"].get.return_value = negociacao

    resultado = atualizar_status_negociacao(1, "cancelado", 20)

    # Verifica se o status foi atualizado
    assert negociacao.status == "Cancelado"

    # Verifica se o retorno indica sucesso
    assert resultado[1] == 200

    # Resultado esperado: comprador pode cancelar pedido aceito.


def test_atualizar_status_vendedor_cancela_pedido_aceito(db_mock):
    negociacao = Negociacao()
    negociacao.vendedor_id = 10
    negociacao.comprador_id = 20
    negociacao.status = "aceito"

    db_mock["session"].get.return_value = negociacao

    resultado = atualizar_status_negociacao(1, "cancelado", 10)

    # Verifica se o status foi atualizado
    assert negociacao.status == "Cancelado"

    # Verifica se o retorno indica sucesso
    assert resultado[1] == 200

    # Resultado esperado: vendedor pode cancelar pedido aceito.


def test_atualizar_status_produtor_tenta_aceitar_pedido_ja_aceito(db_mock):
    negociacao = Negociacao()
    negociacao.vendedor_id = 10
    negociacao.comprador_id = 20
    negociacao.status = "aceito"

    db_mock["session"].get.return_value = negociacao

    resultado = atualizar_status_negociacao(1, "aceito", 10)

    # Verifica se a operação foi recusada
    assert resultado[1] == 400

    # Verifica se a transação não foi confirmada
    db_mock["session"].commit.assert_not_called()

    # Resultado esperado: pedido já aceito não pode ser aceito novamente.

def test_atualizar_status_negociacao_erro_no_commit(db_mock):
    negociacao = Negociacao()
    negociacao.id = 1
    negociacao.vendedor_id = 10
    negociacao.comprador_id = 20
    negociacao.status = "pendente"

    db_mock["session"].get.return_value = negociacao

    # Simula uma falha durante a confirmação da transação
    db_mock["session"].commit.side_effect = Exception("Erro no banco de dados")

    with pytest.raises(Exception, match="Erro no banco de dados"):
        atualizar_status_negociacao(1, "aceito", 10)

    # Verifica se o rollback foi executado
    db_mock["session"].rollback.assert_called_once()

    # Verifica se a sessão foi fechada
    db_mock["session"].close.assert_called_once()

    # Resultado esperado: a transação é revertida e a exceção é propagada.
