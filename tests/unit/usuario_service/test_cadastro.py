import pytest

import services.usuario_service as service
from tests.unit.usuario_service.fakes import UsuarioFake


def test_criar_usuario_com_sucesso(banco_mock):
    # Recupera os objetos simulados do banco de dados:
    # db representa a sessão e resultado representa o retorno da consulta.
    db, resultado = banco_mock

    # Simula que nenhum usuario foi encontrado com o usuario informado, podendo prosseguir com o cadastro
    # Pois não tem cadastro se já tem o email
    resultado.scalar_one_or_none.return_value = None

    # Dados utilizados para simular o cadastro de um novo usuário.
    dados = {
        "nome": "Fabricio",
        "email": "fabricio@email.com",
        "senha": "Senha123!",
        "tipo": "produtor",
        "telefone": "11999999999",
        "estado": "SP",
        "cidade": "São Paulo",
    }

    usuario = service.criar_usuario(dados)

    # Verifica se o usuário foi criado com os dados esperados.
    assert usuario.nome == "Fabricio"
    assert usuario.email == "fabricio@email.com"

    # Confirma que a senha armazenada não é igual à senha original.
    # Isso ajuda a verificar se a senha foi transformada em um hash.
    assert usuario.senha != "Senha123!"

    # Verifica se o usuário foi adicionado à sessão do banco.
    db.add.assert_called_once_with(usuario)

    # Verifica se a transação foi confirmada.
    db.commit.assert_called_once()

    # Verifica se o método refresh foi chamado para atualizar o objeto com os dados disponíveis após a persistência.
    db.refresh.assert_called_once_with(usuario)


def test_criar_usuario_com_dados_obrigatorios_ausentes(banco_mock):
    # O resultado da consulta não é necessário neste teste.
    db, _ = banco_mock

    # Verifica se a função lança ValueError quando faltam dados obrigatórios para o cadastro.
    with pytest.raises(ValueError, match="Dados obrigatórios incompletos",):
        service.criar_usuario({
            "nome": "Fabricio",
            "email": "fabricio@email.com",
            # A senha e o tipo não foram informados.
        })

    # Confirma que a transação foi revertida após o erro.
    db.rollback.assert_called_once()
    # Confirma que o cadastro não foi confirmado no banco.
    db.commit.assert_not_called()


def test_criar_usuario_com_email_invalido(banco_mock):
    db, _ = banco_mock

    with pytest.raises(ValueError, match="Formato de e-mail inválido",):
        service.criar_usuario({
            "nome": "Fabricio",
            "email": "email-invalido",
            "senha": "Senha123!",
            "tipo": "produtor",
        })

    db.rollback.assert_called_once()
    db.commit.assert_not_called()


def test_criar_usuario_com_email_existente(banco_mock):
    db, resultado = banco_mock

    # Simula uma consulta que encontrou um usuário com esse e-mail.
    # UsuarioFake representa o usuário existente, sem acessar o banco real.
    resultado.scalar_one_or_none.return_value = UsuarioFake(
        email="fabricio@email.com"
    )

    with pytest.raises(ValueError, match="Dados inválidos"):
        service.criar_usuario({
            "nome": "Fabricio",
            "email": "fabricio@email.com",
            "senha": "Senha123!",
            "tipo": "produtor",
        })

    db.rollback.assert_called_once()
    db.commit.assert_not_called()


def test_criar_usuario_com_erro_interno(banco_mock):
    db, _ = banco_mock

    # Configura a consulta para lançar um erro inesperado.
    # Isso simula uma falha durante a interação com o banco de dados.
    db.execute.side_effect = RuntimeError(
        "Erro simulado no banco"
    )

    with pytest.raises(
        Exception,
        match="Não foi possível processar o cadastro no momento",
    ):
        service.criar_usuario({
            "nome": "Fabricio",
            "email": "fabricio@email.com",
            "senha": "Senha123!",
            "tipo": "produtor",
        })

    db.rollback.assert_called_once()
    db.commit.assert_not_called()