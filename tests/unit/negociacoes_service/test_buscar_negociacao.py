from services.negociacoes_service import buscar_negociacao
from models import Negociacao


def test_buscar_negociacao_existente(db_mock):
    negociacao = Negociacao()
    negociacao.id = 1

    # Simula o resultado da consulta
    db_mock["session"].execute.return_value.scalar_one_or_none.return_value = negociacao

    resultado = buscar_negociacao(1)

    # Verifica se a consulta foi executada
    db_mock["session"].execute.assert_called_once()

    # Verifica se a negociação retornada é a esperada
    assert resultado == negociacao

    # Verifica se o ID da negociação está correto
    assert resultado.id == 1

    # Verifica se a sessão foi fechada
    db_mock["session"].close.assert_called_once()

    # Resultado esperado: retorna a negociação encontrada.


def test_buscar_negociacao_inexistente(db_mock):
    # Simula uma consulta sem resultados
    db_mock["session"].execute.return_value.scalar_one_or_none.return_value = None

    resultado = buscar_negociacao(999)

    # Verifica se a consulta foi executada
    db_mock["session"].execute.assert_called_once()

    # Verifica se o resultado é None
    assert resultado is None

    # Verifica se a sessão foi fechada
    db_mock["session"].close.assert_called_once()

    # Resultado esperado: retorna None quando a negociação não existe.
