
from types import SimpleNamespace
from unittest.mock import MagicMock

import services.chat_service as service

from tests.unit.chat_service.fakes import ConversaFake, NegociacaoFake


def test_listar_conversas_com_sucesso(
    banco_mock, banco_chat_mock, monkeypatch
):
    # Cria uma conversa fictícia.
    conversa = ConversaFake(id=1,negociacao_id=10,data_criacao="2026-10-29")
    # Cria o outro participante da negociação.
    vendedor = SimpleNamespace( id=20,nome="João",tipo="produtor",foto_perfil="joao.png")
    # Cria um produto fictício.
    produto = SimpleNamespace(nome="Tomate")
    # Cria uma negociação fictícia.
    negociacao = NegociacaoFake(
        id=10,
        comprador_id=5,
        vendedor_id=20,
        vendedor=vendedor,
        comprador=None,
        produto=produto,
        status="aceito"
    )

    # Configura a consulta para retornar a conversa.
    query_mock = banco_chat_mock.query.return_value
    query_mock.order_by.return_value.all.return_value = [conversa]

    # Simula a busca da negociação no banco principal.
    banco_mock.get.return_value = negociacao

    # Substitui a criação da sessão principal pelo banco fictício.
    monkeypatch.setattr(service, "SessionLocal", lambda: banco_mock)

    # Simula a busca da última mensagem.
    ultima_mensagem = SimpleNamespace(texto="Tenho interesse no produto.",data_envio="2026-10-29")

    monkeypatch.setattr(
        service,
        "buscar_ultima_mensagem",
        lambda db, negociacao_id: ultima_mensagem
    )

    # Simula a contagem de mensagens não lidas.
    monkeypatch.setattr(
        service,
        "contar_mensagens_nao_lidas",
        lambda db, negociacao_id, usuario_id: 3
    )

    # Simula a geração da URL da foto de perfil.
    monkeypatch.setattr(
        service,
        "gerar_url_sas",
        lambda container, arquivo: "https://exemplo.com/joao.png"
    )

    # Executa a listagem para o comprador de ID 5.
    resultado = service.listar_conversas(5, banco_chat_mock)

    # Verifica se foi retornada uma conversa.
    assert len(resultado) == 1

    # Verifica os dados principais da conversa.
    assert resultado[0]["conversa_id"] == 1
    assert resultado[0]["negociacao_id"] == 10
    assert resultado[0]["usuario_id"] == 20
    assert resultado[0]["nome"] == "João"
    assert resultado[0]["tipo"] == "produtor"

    # Verifica os dados do produto.
    assert resultado[0]["produto"] == "Tomate"

    # Verifica os dados da última mensagem.
    assert resultado[0]["ultima_mensagem"] == "Tenho interesse no produto."
    assert resultado[0]["tem_mensagens"] is True

    # Verifica a quantidade de mensagens não lidas.
    assert resultado[0]["mensagens_nao_lidas"] == 3

    # Verifica a URL da foto de perfil.
    assert resultado[0]["foto_perfil"] == "https://exemplo.com/joao.png"

    # Verifica se a sessão principal foi fechada.
    banco_mock.close.assert_called_once()


# =========================================================
# TESTE: LISTAR CONVERSAS SEM CONVERSAS
# =========================================================

def test_listar_conversas_sem_conversas(
    banco_mock, banco_chat_mock, monkeypatch
):
    # Configura a consulta para retornar uma lista vazia.
    query_mock = banco_chat_mock.query.return_value
    query_mock.order_by.return_value.all.return_value = []

    # Substitui a criação da sessão principal.
    monkeypatch.setattr(service, "SessionLocal", lambda: banco_mock)

    # Executa a listagem.
    resultado = service.listar_conversas(5, banco_chat_mock)

    # Verifica se nenhuma conversa foi retornada.
    assert resultado == []

    # Verifica se a sessão principal foi fechada.
    banco_mock.close.assert_called_once()


# =========================================================
# TESTE: NEGOCIAÇÃO INEXISTENTE
# =========================================================

def test_listar_conversas_com_negociacao_inexistente(
    banco_mock, banco_chat_mock, monkeypatch
):
    conversa = ConversaFake(
        id=1,
        negociacao_id=999,
        data_criacao="2026-10-29"
    )

    # Configura a consulta para retornar a conversa.
    query_mock = banco_chat_mock.query.return_value
    query_mock.order_by.return_value.all.return_value = [conversa]

    # Simula uma negociação inexistente.
    banco_mock.get.return_value = None

    # Substitui a criação da sessão principal.
    monkeypatch.setattr(service, "SessionLocal", lambda: banco_mock)

    # Executa a listagem.
    resultado = service.listar_conversas(5, banco_chat_mock)

    # Verifica se a conversa foi ignorada.
    assert resultado == []

    # Verifica se a negociação foi consultada.
    banco_mock.get.assert_called_once_with(service.Negociacao, 999)

    # Verifica se a sessão foi fechada.
    banco_mock.close.assert_called_once()


# =========================================================
# TESTE: USUÁRIO SEM ACESSO À NEGOCIAÇÃO
# =========================================================

def test_listar_conversas_sem_acesso(
    banco_mock, banco_chat_mock, monkeypatch
):
    # Cria uma conversa fictícia.
    conversa = ConversaFake(
        id=1,
        negociacao_id=10,
        data_criacao="2026-10-29"
    )

    # Cria uma negociação com comprador 5 e vendedor 20.
    negociacao = NegociacaoFake(
        id=10,
        comprador_id=5,
        vendedor_id=20
    )

    # Configura a consulta para retornar a conversa.
    query_mock = banco_chat_mock.query.return_value
    query_mock.order_by.return_value.all.return_value = [conversa]

    # Simula a busca da negociação.
    banco_mock.get.return_value = negociacao

    # Substitui a criação da sessão principal.
    monkeypatch.setattr(service, "SessionLocal", lambda: banco_mock)

    # Executa a listagem para um usuário que não participa da negociação.
    resultado = service.listar_conversas(30, banco_chat_mock)

    # Verifica se a conversa foi ignorada.
    assert resultado == []

    # Verifica se a sessão foi fechada.
    banco_mock.close.assert_called_once()


# =========================================================
# TESTE: OUTRO PARTICIPANTE INEXISTENTE
# =========================================================

def test_listar_conversas_sem_outro_participante(
    banco_mock, banco_chat_mock, monkeypatch
):
    # Cria uma conversa fictícia.
    conversa = ConversaFake(
        id=1,
        negociacao_id=10,
        data_criacao="2026-10-29"
    )

    # O usuário 5 é comprador, mas o vendedor não está disponível.
    negociacao = NegociacaoFake(
        id=10,
        comprador_id=5,
        vendedor_id=20,
        vendedor=None,
        comprador=None
    )

    # Configura a consulta para retornar a conversa.
    query_mock = banco_chat_mock.query.return_value
    query_mock.order_by.return_value.all.return_value = [conversa]

    # Simula a busca da negociação.
    banco_mock.get.return_value = negociacao

    # Substitui a criação da sessão principal.
    monkeypatch.setattr(service, "SessionLocal", lambda: banco_mock)

    # Executa a listagem.
    resultado = service.listar_conversas(5, banco_chat_mock)

    # Verifica se a conversa foi ignorada.
    assert resultado == []

    # Verifica se a sessão foi fechada.
    banco_mock.close.assert_called_once()
