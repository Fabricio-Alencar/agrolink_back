import pytest

from services.perfil_service import obter_perfil_usuario


def test_obter_perfil_usuario_sucesso(db, usuario):
    resultado = obter_perfil_usuario(1)

    assert resultado == usuario
    assert db.closed is True


def test_obter_perfil_usuario_inexistente(db):
    db.usuario = None

    with pytest.raises(Exception, match="Usuário não encontrado"):
        obter_perfil_usuario(999)

    assert db.closed is True