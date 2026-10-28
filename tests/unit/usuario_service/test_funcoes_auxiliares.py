
import pytest

from services.usuario_service import (
    sanitizar_input,
    validar_email,
    hash_senha,
    verificar_senha,
)


# =========================
# TESTES DE SANITIZAÇÃO
# =========================

def test_sanitizar_input_remove_espacos():
    assert sanitizar_input("  Fabricio  ") == "Fabricio"


def test_sanitizar_input_preserva_valor_nao_textual():
    assert sanitizar_input(123) == 123


def test_sanitizar_input_preserva_none():
    assert sanitizar_input(None) is None


def test_sanitizar_input_string_vazia():
    assert sanitizar_input("   ") == ""


# =========================
# TESTES DE VALIDAÇÃO DE E-MAIL
# =========================

@pytest.mark.parametrize(
    "email",
    [
        "usuario@email.com",
        "fabricio.alencar@empresa.com.br",
        "usuario_123@dominio.org",
    ],
)
def test_validar_email_valido(email):
    assert validar_email(email) is True


@pytest.mark.parametrize(
    "email",
    [
        "",
        None,
        "emailinvalido",
        "usuario@",
        "@dominio.com",
        "usuario@dominio",
    ],
)
def test_validar_email_invalido(email):
    assert validar_email(email) is False


# =========================
# TESTES DE HASH DE SENHA
# =========================

def test_hash_senha_nao_retorna_senha_original():
    senha = "SenhaSegura123!"
    senha_hash = hash_senha(senha)
    assert senha_hash != senha


def test_verificar_senha_correta():
    senha = "SenhaSegura123!"
    senha_hash = hash_senha(senha)
    assert verificar_senha(senha_hash, senha) is True


def test_verificar_senha_incorreta():
    senha_hash = hash_senha("SenhaSegura123!")
    assert verificar_senha(senha_hash, "SenhaErrada456!") is False
