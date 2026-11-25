from io import BytesIO
from types import SimpleNamespace

import pytest

from services import perfil_service
from services.perfil_service import atualizar_perfil_usuario


def test_atualizar_dados_gerais(db, usuario):
    dados = {
        "nome": "Novo Nome",
        "email": "novo@email.com",
        "telefone": "11888888888",
        "cidade": "Campinas",
        "estado": "SP"
    }

    resultado = atualizar_perfil_usuario(1, dados, None)

    assert resultado.nome == "Novo Nome"
    assert resultado.email == "novo@email.com"
    assert resultado.telefone == "11888888888"
    assert resultado.cidade == "Campinas"
    assert resultado.estado == "SP"
    assert db.committed is True
    assert db.closed is True


def test_atualizar_senha(db, usuario, monkeypatch):
    monkeypatch.setattr(
        perfil_service,
        "generate_password_hash",
        lambda senha: f"hash_{senha}"
    )

    atualizar_perfil_usuario(
        1,
        {"senha": "nova_senha"},
        None
    )

    assert usuario.senha == "hash_nova_senha"


@pytest.mark.parametrize("senha", ["", "   ", "••••••••"])
def test_nao_atualizar_senha_vazia_ou_mascarada(
    db,
    usuario,
    senha
):
    senha_antiga = usuario.senha

    atualizar_perfil_usuario(
        1,
        {"senha": senha},
        None
    )

    assert usuario.senha == senha_antiga


def test_atualizar_foto_perfil(db, usuario, monkeypatch):
    arquivos_enviados = []

    monkeypatch.setattr(
        perfil_service,
        "upload_arquivo",
        lambda arquivo, nome, container: arquivos_enviados.append(nome)
    )

    monkeypatch.setattr(
        perfil_service,
        "deletar_arquivo",
        lambda nome, container: None
    )

    arquivo = SimpleNamespace(
        filename="nova_foto.PNG",
        file=BytesIO(b"imagem")
    )

    atualizar_perfil_usuario(1, {}, arquivo)

    assert len(arquivos_enviados) == 1
    assert arquivos_enviados[0].endswith(".png")
    assert usuario.foto_perfil == arquivos_enviados[0]


def test_excluir_foto_antiga_ao_atualizar(db, usuario, monkeypatch):
    fotos_excluidas = []

    monkeypatch.setattr(
        perfil_service,
        "upload_arquivo",
        lambda *args: None
    )

    monkeypatch.setattr(
        perfil_service,
        "deletar_arquivo",
        lambda nome, container: fotos_excluidas.append(nome)
    )

    arquivo = SimpleNamespace(
        filename="nova.jpg",
        file=BytesIO(b"imagem")
    )

    atualizar_perfil_usuario(1, {}, arquivo)

    assert "foto_antiga.png" in fotos_excluidas


@pytest.mark.parametrize(
    "foto_antiga",
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
    foto_antiga
):
    usuario.foto_perfil = foto_antiga

    fotos_excluidas = []

    monkeypatch.setattr(
        perfil_service,
        "upload_arquivo",
        lambda *args: None
    )

    monkeypatch.setattr(
        perfil_service,
        "deletar_arquivo",
        lambda nome, container: fotos_excluidas.append(nome)
    )

    arquivo = SimpleNamespace(
        filename="nova.jpg",
        file=BytesIO(b"imagem")
    )

    atualizar_perfil_usuario(1, {}, arquivo)

    assert fotos_excluidas == []


def test_rollback_quando_commit_falha(db):
    db.commit_error = Exception("Erro no banco")

    with pytest.raises(Exception, match="Erro ao atualizar perfil"):
        atualizar_perfil_usuario(1, {}, None)

    assert db.rolled_back is True
    assert db.closed is True


def test_invalidar_cache_quando_produtor_atualiza_perfil(
    db,
    redis,
    usuario
):
    usuario.tipo = "produtor"

    atualizar_perfil_usuario(1, {}, None)

    assert "marketplace" in redis.deleted_keys


def test_nao_invalidar_cache_quando_comprador_atualiza_perfil(
    db,
    redis,
    usuario
):
    usuario.tipo = "comprador"

    atualizar_perfil_usuario(1, {}, None)

    assert redis.deleted_keys == []


def test_atualizar_usuario_inexistente(db):
    db.usuario = None

    with pytest.raises(Exception, match="Usuário não encontrado"):
        atualizar_perfil_usuario(999, {}, None)

    assert db.closed is True