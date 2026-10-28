
import pytest

import services.usuario_service as service
from tests.unit.usuario_service.fakes import UsuarioFake


def test_login_com_sucesso(banco_mock):
    _, resultado = banco_mock

    usuario = UsuarioFake(
        nome="Fabricio",
        email="fabricio@email.com",
        senha=service.hash_senha("Senha123!"),
        tipo="produtor",
    )

    resultado.scalar_one_or_none.return_value = usuario

    resultado_login = service.login_usuario({
        "email": "fabricio@email.com",
        "senha": "Senha123!",
        "tipo": "produtor",
    })

    assert resultado_login is usuario


@pytest.mark.parametrize(
    "dados",
    [
        {},
        {"email": "fabricio@email.com"},
        {"senha": "Senha123!"},
        {
            "email": "email-invalido",
            "senha": "Senha123!",
        },
    ],
)

def test_login_com_credenciais_invalidas(banco_mock, dados):
    with pytest.raises(ValueError, match="Credenciais inválidas",):
        service.login_usuario(dados)


def test_login_com_usuario_inexistente(banco_mock):
    with pytest.raises(ValueError, match="Credenciais inválidas",):
        service.login_usuario({
            "email": "inexistente@email.com",
            "senha": "Senha123!",
        })


def test_login_com_senha_incorreta(banco_mock):
    _, resultado = banco_mock

    resultado.scalar_one_or_none.return_value = UsuarioFake(
        email="fabricio@email.com",
        senha=service.hash_senha("SenhaCorreta123!"),
        tipo="produtor",
    )

    with pytest.raises(ValueError,match="Credenciais inválidas",):
        service.login_usuario({
            "email": "fabricio@email.com",
            "senha": "SenhaErrada123!",
        })


def test_login_com_tipo_de_usuario_incorreto(banco_mock):
    _, resultado = banco_mock

    resultado.scalar_one_or_none.return_value = UsuarioFake(
        email="fabricio@email.com",
        senha=service.hash_senha("Senha123!"),
        tipo="produtor",
    )

    with pytest.raises(ValueError,match="Credenciais inválidas",):
        service.login_usuario({
            "email": "fabricio@email.com",
            "senha": "Senha123!",
            "tipo": "estabelecimento",
        })


def test_login_com_erro_interno(banco_mock):
    db, _ = banco_mock

    db.execute.side_effect = RuntimeError("Erro simulado no banco")

    with pytest.raises(Exception,match="Não foi possível realizar o login",):
        service.login_usuario({
            "email": "fabricio@email.com",
            "senha": "Senha123!",
        })

    db.close.assert_called_once()
