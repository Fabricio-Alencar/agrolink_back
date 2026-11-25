import pytest

from services import perfil_service
from services.perfil_service import excluir_conta_usuario


def test_excluir_conta_com_sucesso(db, usuario, monkeypatch):
    monkeypatch.setattr(
        perfil_service,
        "deletar_arquivo",
        lambda *args: None
    )

    resultado = excluir_conta_usuario(1)

    assert resultado is True
    assert db.deleted == usuario
    assert db.committed is True
    assert db.closed is True


def test_excluir_conta_inexistente(db):
    db.usuario = None

    with pytest.raises(Exception, match="Usuário não encontrado"):
        excluir_conta_usuario(999)

    assert db.closed is True


def test_excluir_foto_do_azure(db, usuario, monkeypatch):
    fotos_excluidas = []

    monkeypatch.setattr(
        perfil_service,
        "deletar_arquivo",
        lambda nome, container: fotos_excluidas.append(nome)
    )

    excluir_conta_usuario(1)

    assert "foto_antiga.png" in fotos_excluidas


@pytest.mark.parametrize(
    "foto",
    [
        "user.webp",
        "https://exemplo.com/foto.png",
        "http://exemplo.com/foto.png"
    ]
)
def test_nao_excluir_foto_padrao_ou_externa(
    db,
    usuario,
    monkeypatch,
    foto
):
    usuario.foto_perfil = foto

    fotos_excluidas = []

    monkeypatch.setattr(
        perfil_service,
        "deletar_arquivo",
        lambda nome, container: fotos_excluidas.append(nome)
    )

    excluir_conta_usuario(1)

    assert fotos_excluidas == []


def test_continuar_exclusao_se_azure_falhar(
    db,
    monkeypatch
):
    def falhar_exclusao(*args):
        raise Exception("Erro no Azure")

    monkeypatch.setattr(
        perfil_service,
        "deletar_arquivo",
        falhar_exclusao
    )

    resultado = excluir_conta_usuario(1)

    assert resultado is True
    assert db.committed is True


def test_invalidar_cache_ao_excluir_produtor(
    db,
    redis,
    usuario,
    monkeypatch
):
    usuario.tipo = "produtor"

    monkeypatch.setattr(
        perfil_service,
        "deletar_arquivo",
        lambda *args: None
    )

    excluir_conta_usuario(1)

    assert "marketplace" in redis.deleted_keys


def test_nao_invalidar_cache_ao_excluir_comprador(
    db,
    redis,
    usuario,
    monkeypatch
):
    usuario.tipo = "comprador"

    monkeypatch.setattr(
        perfil_service,
        "deletar_arquivo",
        lambda *args: None
    )

    excluir_conta_usuario(1)

    assert redis.deleted_keys == []


def test_rollback_se_falhar_ao_excluir_conta(
    db,
    monkeypatch
):
    db.delete_error = Exception("Erro no banco")

    monkeypatch.setattr(
        perfil_service,
        "deletar_arquivo",
        lambda *args: None
    )

    with pytest.raises(Exception, match="Erro ao excluir conta"):
        excluir_conta_usuario(1)

    assert db.rolled_back is True
    assert db.closed is True