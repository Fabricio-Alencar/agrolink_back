from unittest.mock import MagicMock

import pytest

import services.usuario_service as service


@pytest.fixture
def banco_mock(monkeypatch):
    """Simula a sessão do banco de dados e o resultado de uma consulta."""

    # Cria um objeto falso que simula a sessão do banco de dados.
    db = MagicMock()

    # Cria um objeto falso que simula o resultado de uma consulta.
    resultado = MagicMock()

    # Configura a execução de uma consulta para retornar o resultado simulado.
    db.execute.return_value = resultado

    # scalar_one_or_none() retorna o usuário encontrado pela consulta ou None se nenhum usuário for encontrado.
    resultado.scalar_one_or_none.return_value = None

    # Substitui a criação da sessão real pela sessão simulada durante o teste.
    monkeypatch.setattr(service, "SessionLocal", lambda: db)

    # Retorna os dois objetos simulados para serem utilizados nos testes.
    return db, resultado
