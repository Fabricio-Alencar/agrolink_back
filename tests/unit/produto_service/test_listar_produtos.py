import pytest

import services.produto_service as service
from tests.unit.produto_service.fakes import UsuarioFake, ProdutoFake


def test_listar_produtos_com_sucesso(banco_mock):
    # Recupera a sessão simulada do banco de dados.
    db = banco_mock

    # Cria uma lista de produtos falsos para simular o resultado da consulta.
    produtos_esperados = [
        ProdutoFake(id=1, nome="Tomate", produtor_id=10),
        ProdutoFake(id=2, nome="Alface", produtor_id=10),
    ]

    # Configura a consulta para retornar a lista de produtos simulada.
    db.execute.return_value.scalars.return_value.all.return_value = produtos_esperados

    # Executa a função que está sendo testada.
    produtos = service.listar_produtos_produtor(10)

    # Verifica se a função retornou os produtos esperados.
    assert produtos == produtos_esperados

    # Verifica se a consulta foi executada.
    db.execute.assert_called_once()
    # Verifica se a sessão do banco foi fechada.
    db.close.assert_called_once()


def test_listar_produtos_de_produtor_sem_produtos(banco_mock):
    db = banco_mock

    # Simula uma consulta que não encontrou produtos.
    produtos_esperados = []
    
    db.execute.return_value.scalars.return_value.all.return_value = produtos_esperados

    # Executa a função.
    produtos = service.listar_produtos_produtor(40)

    # Verifica se a função retornou uma lista vazia.
    assert produtos == []

    # Verifica se a consulta foi executada.
    db.execute.assert_called_once()

    # Verifica se a sessão foi fechada.
    db.close.assert_called_once()

def test_listar_produtos_filtra_pelo_produtor_informado(banco_mock):
    db = banco_mock
    # Simula uma consulta que não encontrou produtos.
    db.execute.return_value.scalars.return_value.all.return_value = []

    service.listar_produtos_produtor(40)
    # Obtém a consulta SQLAlchemy que foi passada para db.execute().
    consulta = db.execute.call_args.args[0]

    # Compila a consulta e obtém um dicionário com os parâmetros utilizados nela, incluindo o ID do produtor informado.
    parametros = consulta.compile().params

    # Verifica se o parametro 40 (id do produtor) está nos parametros de consulta
    assert 40 in parametros.values() 

def test_listar_produtos_fecha_banco_se_ocorrer_erro(banco_mock):
    db = banco_mock

    db.execute.side_effect = Exception("Erro de consulta")

    with pytest.raises(Exception, match="Erro de consulta"):
        service.listar_produtos_produtor(10)

    db.close.assert_called_once()

