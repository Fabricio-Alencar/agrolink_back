
import os
import subprocess
import sys


def executar_importacao(ambiente):
    codigo = """
import services.cache_service
"""

    return subprocess.run(
        [sys.executable, "-c", codigo],
        env=ambiente,
        capture_output=True,
        text=True,
        timeout=10
    )


def test_erro_quando_redis_host_nao_definido():
    ambiente = os.environ.copy()

    # Impede o carregamento do arquivo .env
    ambiente["PYTHON_DOTENV_DISABLED"] = "1"

    ambiente.pop("REDIS_HOST", None)
    ambiente["REDIS_PASSWORD"] = "senha_ficticia"

    resultado = executar_importacao(ambiente)

    assert resultado.returncode != 0
    assert "REDIS_HOST não foi definida" in resultado.stderr


def test_erro_quando_redis_password_nao_definida():
    ambiente = os.environ.copy()

    # Impede o carregamento do arquivo .env
    ambiente["PYTHON_DOTENV_DISABLED"] = "1"

    ambiente["REDIS_HOST"] = "localhost"
    ambiente.pop("REDIS_PASSWORD", None)

    resultado = executar_importacao(ambiente)

    assert resultado.returncode != 0
    assert "REDIS_PASSWORD não foi definida" in resultado.stderr
