import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

from auth.dependencies import get_current_user
from models.usuario import Usuario

def test_get_current_user_sem_token(db_mock):
    """Verifica se a função rejeita uma requisição sem token."""

    with patch("auth.dependencies.decodificar_token") as decodificar_mock:
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(None)

        decodificar_mock.assert_not_called()

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Usuário não autenticado"


def test_get_current_user_sucesso(db_mock):
    """Verifica se retorna os dados do usuário quando o token é válido."""

    usuario = MagicMock()
    usuario.id = 10
    usuario.tipo = "produtor"
    usuario.nome = "João"

    db_mock["session"].get.return_value = usuario

    with patch(
        "auth.dependencies.decodificar_token",
        return_value={"sub": "10", "tipo": "produtor"}
    ):
        resultado = get_current_user("token_valido")

    assert resultado == {
        "user_id": 10,
        "tipo": "produtor",
        "nome": "João"
    }

    # Verifica se buscou o usuário pelo ID correto.
    db_mock["session"].get.assert_called_once_with(Usuario, 10)

    # Verifica se a sessão foi encerrada.
    db_mock["session"].close.assert_called_once()


@pytest.mark.parametrize(
    "payload",
    [
        {"tipo": "produtor"},
        {"sub": "10"},
        {},
    ]
)
def test_get_current_user_payload_incompleto(db_mock, payload):
    """Verifica se rejeita tokens sem os dados necessários."""

    with patch(
        "auth.dependencies.decodificar_token",
        return_value=payload
    ):
        with pytest.raises(HTTPException) as exc_info:
            get_current_user("token_valido")

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Token inválido"

    # O banco não deve ser consultado.
    db_mock["session_local"].assert_not_called()


def test_get_current_user_usuario_inexistente(db_mock):
    """Verifica se rejeita o token quando o usuário não existe no banco."""

    db_mock["session"].get.return_value = None

    with patch(
        "auth.dependencies.decodificar_token",
        return_value={"sub": "10", "tipo": "produtor"}
    ):
        with pytest.raises(HTTPException) as exc_info:
            get_current_user("token_valido")

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Usuário não encontrado"

    # Verifica se a sessão foi encerrada.
    db_mock["session"].close.assert_called_once()


def test_get_current_user_token_invalido(db_mock):
    """Verifica se trata erros durante a decodificação do token."""

    with patch(
        "auth.dependencies.decodificar_token",
        side_effect=Exception("Token expirado")
    ):
        with pytest.raises(HTTPException) as exc_info:
            get_current_user("token_invalido")

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Token inválido ou expirado"

    # O banco não deve ser acessado.
    db_mock["session_local"].assert_not_called()


def test_get_current_user_id_invalido(db_mock):
    """Verifica se trata IDs que não podem ser convertidos para inteiro."""

    with patch(
        "auth.dependencies.decodificar_token",
        return_value={"sub": "abc", "tipo": "produtor"}
    ):
        with pytest.raises(HTTPException) as exc_info:
            get_current_user("token_valido")

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Token inválido ou expirado"

    # Verifica se a sessão foi encerrada.
    db_mock["session"].close.assert_called_once()