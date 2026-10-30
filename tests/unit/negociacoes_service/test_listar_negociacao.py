
from services.negociacoes_service import listar_negociacoes
from models import Usuario, Negociacao


def test_listar_negociacoes_como_produtor(db_mock):
    usuario = Usuario()
    negociacoes = [Negociacao(), Negociacao()]

    db_mock["session"].get.return_value = usuario

    resultado_consulta = db_mock["session"].execute.return_value
    resultado_consulta.scalars.return_value.all.return_value = negociacoes

    resultado = listar_negociacoes(1, "produtor")

    # Verifica se o usuário foi consultado
    db_mock["session"].get.assert_called_once_with(Usuario, 1)

    # Verifica se a consulta foi executada
    db_mock["session"].execute.assert_called_once()

    # Verifica se as negociações foram retornadas
    assert resultado == negociacoes

    # Verifica se a sessão foi fechada
    db_mock["session"].close.assert_called_once()

    # Resultado esperado: negociações do produtor retornadas corretamente.


def test_listar_negociacoes_como_estabelecimento(db_mock):
    usuario = Usuario()
    negociacoes = [Negociacao()]

    db_mock["session"].get.return_value = usuario

    resultado_consulta = db_mock["session"].execute.return_value
    resultado_consulta.scalars.return_value.all.return_value = negociacoes

    resultado = listar_negociacoes(2, "estabelecimento")

    # Verifica se o usuário foi consultado
    db_mock["session"].get.assert_called_once_with(Usuario, 2)

    # Verifica se a consulta foi executada
    db_mock["session"].execute.assert_called_once()

    # Verifica se as negociações foram retornadas
    assert resultado == negociacoes

    # Verifica se a sessão foi fechada
    db_mock["session"].close.assert_called_once()

    # Resultado esperado: negociações do estabelecimento retornadas corretamente.


def test_listar_negociacoes_usuario_inexistente(db_mock):
    db_mock["session"].get.return_value = None

    resultado = listar_negociacoes(999, "produtor")

    # Verifica se o usuário foi consultado
    db_mock["session"].get.assert_called_once_with(Usuario, 999)

    # Verifica se a consulta de negociações não foi executada
    db_mock["session"].execute.assert_not_called()

    # Verifica se o resultado é uma lista vazia
    assert resultado == []

    # Verifica se a sessão foi fechada
    db_mock["session"].close.assert_called_once()

    # Resultado esperado: lista vazia quando o usuário não existe.


def test_listar_negociacoes_tipo_invalido(db_mock):
    db_mock["session"].get.return_value = Usuario()

    resultado = listar_negociacoes(1, "administrador")

    # Verifica se a consulta de negociações não foi executada
    db_mock["session"].execute.assert_not_called()

    # Verifica se o resultado é uma lista vazia
    assert resultado == []

    # Verifica se a sessão foi fechada
    db_mock["session"].close.assert_called_once()

    # Resultado esperado: lista vazia quando o tipo de negociante é inválido.
