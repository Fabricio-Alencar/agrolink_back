from services.chat_service import usuario_tem_acesso
import services.chat_service as service

from tests.unit.chat_service.fakes import NegociacaoFake


def test_usuario_tem_acesso_como_comprador():
    negociacao = NegociacaoFake(
        comprador_id=10,
        vendedor_id=20
    )
    resultado = usuario_tem_acesso(negociacao, 10)
    assert resultado is True


def test_usuario_tem_acesso_como_vendedor():
    negociacao = NegociacaoFake(
        comprador_id=10,
        vendedor_id=20
    )
    resultado = usuario_tem_acesso(negociacao, 20)
    assert resultado is True


def test_usuario_sem_acesso_a_negociacao():
    negociacao = NegociacaoFake(
        comprador_id=10,
        vendedor_id=20
    )
    resultado = usuario_tem_acesso(negociacao, 30)
    assert resultado is False


def test_usuario_tem_acesso_com_negociacao_inexistente():
    resultado = usuario_tem_acesso(None, 10)
    assert resultado is False

def test_buscar_negociacao_com_sucesso(banco_mock, monkeypatch):
    negociacao = NegociacaoFake(id=1)
    banco_mock.get.return_value = negociacao

    monkeypatch.setattr(service, "SessionLocal", lambda: banco_mock)

    resultado = service.buscar_negociacao(1)

    assert resultado == negociacao

    banco_mock.get.assert_called_once_with(service.Negociacao, 1)
    banco_mock.close.assert_called_once()


def test_buscar_negociacao_inexistente(banco_mock, monkeypatch):
    banco_mock.get.return_value = None

    monkeypatch.setattr(service, "SessionLocal", lambda: banco_mock)

    resultado = service.buscar_negociacao(999)

    assert resultado is None    