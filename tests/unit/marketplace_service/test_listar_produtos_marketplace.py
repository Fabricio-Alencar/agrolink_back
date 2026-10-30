
import json
from unittest.mock import MagicMock

import services.marketplace_service as service


def test_listar_produtos_retorna_dados_do_cache(monkeypatch):
    dados_cache = [
        {"id": 1, "nome": "Tomate", "preco": 5.0}
    ]

    redis_mock = MagicMock()
    redis_mock.get.return_value = json.dumps(dados_cache)

    monkeypatch.setattr(service, "redis_client", redis_mock)

    resultado = service.listar_produtos()

    assert resultado == dados_cache
    redis_mock.get.assert_called_once_with(service.CACHE_KEY)
    redis_mock.set.assert_not_called()


def test_listar_produtos_consulta_banco_e_salva_cache(
    monkeypatch, banco_mock, produto_fake, produtor_fake
):
    produto = produto_fake
    produto.nome = "Tomate"
    produto.preco = 5.50
    produto.quantidade = 10
    produto.unidade = "kg"
    produto.categoria = "Legumes"
    produto.descricao = "Tomate fresco"
    produto.foto = "tomate.jpg"
    produto.status = "publicado"
    produto.produtor = produtor_fake

    # Simula o retorno da consulta ao banco.
    resultado_consulta = MagicMock()
    resultado_consulta.scalars.return_value.all.return_value = [produto]

    banco_mock.execute.return_value = resultado_consulta

    # Simula o Redis vazio.
    redis_mock = MagicMock()
    redis_mock.get.return_value = None
    monkeypatch.setattr(service, "redis_client", redis_mock)

    # Simula o resumo das avaliações.
    avaliacoes = {
        produto.produtor_id: {
            "media": 4.5,
            "total": 2
        }
    }
    monkeypatch.setattr(
        service, "resumo_avaliacoes", MagicMock(return_value=avaliacoes)
    )

    resultado = service.listar_produtos()

    assert len(resultado) == 1
    assert resultado[0]["id"] == produto.id
    assert resultado[0]["nome"] == "Tomate"
    assert resultado[0]["preco"] == 5.50
    assert resultado[0]["quantidade"] == 10.0
    assert resultado[0]["produtor_nome"] == produtor_fake.nome
    assert resultado[0]["produtor_avaliacao"] == 4.5
    assert resultado[0]["produtor_total_avaliacoes"] == 2

    # Verifica se os dados foram salvos no Redis.
    redis_mock.set.assert_called_once()
    argumentos = redis_mock.set.call_args

    assert argumentos.args[0] == service.CACHE_KEY
    assert json.loads(argumentos.args[1]) == resultado
    assert argumentos.kwargs["ex"] == service.CACHE_TTL

    banco_mock.close.assert_called_once()


def test_listar_produtos_sem_produtos(
    monkeypatch, banco_mock
):
    # Simula uma consulta sem resultados.
    resultado_consulta = MagicMock()
    resultado_consulta.scalars.return_value.all.return_value = []

    banco_mock.execute.return_value = resultado_consulta

    redis_mock = MagicMock()
    redis_mock.get.return_value = None
    monkeypatch.setattr(service, "redis_client", redis_mock)

    resumo_mock = MagicMock(return_value={})
    monkeypatch.setattr(service, "resumo_avaliacoes", resumo_mock)

    resultado = service.listar_produtos()

    assert resultado == []

    # Não deve tentar buscar avaliações sem produtores.
    resumo_mock.assert_called_once_with(banco_mock, [])

    redis_mock.set.assert_called_once_with(
        service.CACHE_KEY,
        "[]",
        ex=service.CACHE_TTL
    )

    banco_mock.close.assert_called_once()


def test_listar_produtos_sem_avaliacoes(
    monkeypatch, banco_mock, produto_fake, produtor_fake
):
    produto = produto_fake
    produto.nome = "Tomate"
    produto.preco = None
    produto.quantidade = None
    produto.unidade = "kg"
    produto.categoria = "Legumes"
    produto.descricao = None
    produto.foto = None
    produto.status = "publicado"
    produto.produtor = produtor_fake

    resultado_consulta = MagicMock()
    resultado_consulta.scalars.return_value.all.return_value = [produto]
    banco_mock.execute.return_value = resultado_consulta

    redis_mock = MagicMock()
    redis_mock.get.return_value = None
    monkeypatch.setattr(service, "redis_client", redis_mock)

    monkeypatch.setattr(
        service, "resumo_avaliacoes", MagicMock(return_value={})
    )

    resultado = service.listar_produtos()

    assert resultado[0]["preco"] is None
    assert resultado[0]["quantidade"] is None
    assert resultado[0]["descricao"] is None
    assert resultado[0]["foto"] is None
    assert resultado[0]["produtor_avaliacao"] is None
    assert resultado[0]["produtor_total_avaliacoes"] == 0

    banco_mock.close.assert_called_once()


def test_listar_produtos_fecha_banco_se_ocorrer_erro(
    monkeypatch, banco_mock
):
    redis_mock = MagicMock()
    redis_mock.get.return_value = None
    monkeypatch.setattr(service, "redis_client", redis_mock)

    banco_mock.execute.side_effect = Exception("Erro na consulta")

    import pytest

    with pytest.raises(Exception, match="Erro na consulta"):
        service.listar_produtos()

    banco_mock.close.assert_called_once()
