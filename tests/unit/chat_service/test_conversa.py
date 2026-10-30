import services.chat_service as service
from tests.unit.chat_service.fakes import ConversaFake
from unittest.mock import MagicMock
from sqlalchemy.exc import IntegrityError
import pytest



def test_buscar_conversa_com_sucesso(banco_chat_mock, monkeypatch):
    conversa = ConversaFake(id=1, negociacao_id=10)

    query_mock = banco_chat_mock.query.return_value  # Simula o resultado da consulta iniciada pelo query()
    query_mock.filter.return_value.first.return_value = conversa  # Define que a busca filtrada retornará a conversa fictícia

    resultado = service.buscar_conversa(banco_chat_mock, 10)

    assert resultado == conversa

    banco_chat_mock.query.assert_called_once_with(service.Conversa)
    query_mock.filter.assert_called_once()
    query_mock.filter.return_value.first.assert_called_once()


def test_buscar_conversa_inexistente(banco_chat_mock, monkeypatch):
    query_mock = banco_chat_mock.query.return_value
    query_mock.filter.return_value.first.return_value = None

    resultado = service.buscar_conversa(banco_chat_mock, 999)

    assert resultado is None

    banco_chat_mock.query.assert_called_once_with(service.Conversa)
    query_mock.filter.return_value.first.assert_called_once()


def test_iniciar_conversa_ja_existente(banco_chat_mock, monkeypatch):
    conversa = ConversaFake(id=1, negociacao_id=10)

    # Simula uma conversa já existente no banco
    monkeypatch.setattr(
        service,
        "buscar_conversa",
        lambda db, negociacao_id: conversa
    )

    resultado = service.iniciar_conversa(
        banco_chat_mock,
        10,
        20
    )

    assert resultado == conversa  # Verifica se retornou a conversa existente

    banco_chat_mock.add.assert_not_called()  # Verifica se não tentou criar outra conversa
    banco_chat_mock.commit.assert_not_called()  # Verifica se não salvou alterações
    banco_chat_mock.refresh.assert_not_called()  # Verifica se não atualizou o objeto  

def test_iniciar_conversa_com_sucesso(banco_chat_mock, monkeypatch):
    # Simula que nenhuma conversa foi encontrada
    monkeypatch.setattr(
        service,
        "buscar_conversa",
        lambda db, negociacao_id: None
    )

    resultado = service.iniciar_conversa(
        banco_chat_mock,
        10,
        20
    )

    # Verifica se a conversa foi criada com os dados corretos
    assert resultado.negociacao_id == 10
    assert resultado.iniciada_por_id == 20

    # Verifica se a conversa foi adicionada ao banco
    banco_chat_mock.add.assert_called_once_with(resultado)

    # Verifica se as alterações foram salvas
    banco_chat_mock.commit.assert_called_once()

    # Verifica se o objeto foi atualizado após salvar
    banco_chat_mock.refresh.assert_called_once_with(resultado)

    banco_chat_mock.rollback.assert_not_called()      


def test_iniciar_conversa_com_integridade_duplicada(banco_chat_mock, monkeypatch):
    conversa = ConversaFake(id=1, negociacao_id=10)

    # Simula duas consultas:
    # 1ª chamada: não encontra uma conversa.
    # 2ª chamada: encontra a conversa que foi criada por outra requisição.
    buscar_mock = MagicMock(side_effect=[None, conversa])
    monkeypatch.setattr(service, "buscar_conversa", buscar_mock)


    # Simula um erro de integridade quando o método commit() for chamado.
    banco_chat_mock.commit.side_effect = IntegrityError(
        "INSERT",  # Comando SQL que estava sendo executado quando ocorreu o erro.
        {},  # Parâmetros utilizados na operação SQL (vazios neste teste).
        Exception("Registro duplicado")  # Simula a causa do erro: registro duplicado.
    )
    resultado = service.iniciar_conversa(
        banco_chat_mock,
        10,
        20
    )

    assert resultado == conversa  # Verifica se retornou a conversa criada pela outra requisição
    assert buscar_mock.call_count == 2  # Verifica se buscou a conversa novamente

    banco_chat_mock.add.assert_called_once()  # Verifica se tentou adicionar a conversa
    banco_chat_mock.commit.assert_called_once()  # Verifica se tentou salvar
    banco_chat_mock.rollback.assert_called_once()  # Verifica se desfez a transação
    banco_chat_mock.refresh.assert_not_called()  # Não atualizou, pois o commit falhou    


def test_iniciar_conversa_com_erro_sem_conversa_existente(
    banco_chat_mock, monkeypatch
):
    # Simula duas buscas sem encontrar uma conversa.
    buscar_mock = MagicMock(side_effect=[None, None])

    monkeypatch.setattr(service, "buscar_conversa", buscar_mock)

    banco_chat_mock.commit.side_effect = IntegrityError("INSERT",{},Exception("Violação de integridade"))

    # Verifica se o erro é propagado quando nenhuma conversa é encontrada.
    with pytest.raises(IntegrityError):
        service.iniciar_conversa(banco_chat_mock, 10, 20)

    assert buscar_mock.call_count == 2

    # Verifica se a transação foi desfeita.
    banco_chat_mock.rollback.assert_called_once()
    # Verifica se o commit foi tentado uma única vez.
    banco_chat_mock.commit.assert_called_once()
    # Verifica que o refresh não foi executado.
    banco_chat_mock.refresh.assert_not_called()