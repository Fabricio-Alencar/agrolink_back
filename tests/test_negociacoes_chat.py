
import pytest

from types import SimpleNamespace
from fastapi import HTTPException

from routes import negociacoes_routes
from services.chat_service import usuario_tem_acesso


class TestAutorizacaoNegociacoes:

    def test_usuario_nao_consegue_acessar_negociacao_de_outro(
        self, monkeypatch
    ):
        """
        Verifica se um usuário que não participa da negociação
        é impedido de consultar seus detalhes.
        """

        negociacao = SimpleNamespace(
            id=1,
            comprador_id=10,
            vendedor_id=20
        )

        # Simula a busca de uma negociação existente.
        monkeypatch.setattr(
            negociacoes_routes.negociacoes_service,
            "buscar_negociacao",
            lambda negociacao_id: negociacao
        )

        # Usuário 30 não é comprador nem vendedor.
        with pytest.raises(HTTPException) as erro:
            negociacoes_routes.buscar_negociacao_detalhes(
                1,
                {"user_id": 30}
            )

        assert erro.value.status_code == 403
        assert erro.value.detail["erro"] == (
            "Você não possui acesso a esta negociação."
        )


class TestAutorizacaoChat:

    def test_usuario_sem_participacao_nao_tem_acesso_a_conversa(self):
        """
        Verifica se um usuário que não participa da negociação
        é considerado sem permissão para acessar a conversa.
        """

        negociacao = SimpleNamespace(
            id=1,
            comprador_id=10,
            vendedor_id=20
        )

        usuario_externo_id = 30

        permitido = usuario_tem_acesso(
            negociacao,
            usuario_externo_id
        )

        assert permitido is False

    def test_participante_tem_acesso_a_conversa(self):
        """
        Verifica se um participante da negociação
        possui autorização para acessar a conversa.
        """

        negociacao = SimpleNamespace(
            id=1,
            comprador_id=10,
            vendedor_id=20
        )

        assert usuario_tem_acesso(negociacao, 10) is True
        assert usuario_tem_acesso(negociacao, 20) is True
