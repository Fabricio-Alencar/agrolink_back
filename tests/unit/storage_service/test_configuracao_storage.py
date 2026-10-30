
import os
import subprocess
import sys


def test_erro_quando_connection_string_nao_definida():
    ambiente = os.environ.copy()
    ambiente.pop("AZURE_STORAGE_CONNECTION_STRING", None)

    codigo = """
import services.azure_storage_service
"""

    resultado = subprocess.run(
        [sys.executable, "-c", codigo],
        env=ambiente,
        capture_output=True,
        text=True,
        timeout=10
    )

    # Resultado esperado: a importação falha com RuntimeError
    # quando a connection string não está definida.

    assert resultado.returncode != 0
    assert "RuntimeError" in resultado.stderr
    assert "AZURE_STORAGE_CONNECTION_STRING não foi definida" in resultado.stderr
