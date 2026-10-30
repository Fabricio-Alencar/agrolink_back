
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from services.azure_storage_service import gerar_url_sas


def test_gerar_url_sas_com_sucesso(
    azure_mock,
    connection_string_mock
):
    nome_blob = "produto_123.jpg"
    container_nome = "produtos"

    with patch(
        "services.azure_storage_service.generate_blob_sas"
    ) as sas_mock:

        sas_mock.return_value = "token_ficticio"

        resultado = gerar_url_sas(
            container_nome,
            nome_blob
        )

    # Verifica se o SAS foi gerado com os dados corretos
    argumentos = sas_mock.call_args.kwargs

    assert argumentos["account_name"] == "contateste"
    assert argumentos["account_key"] == "chaveficticia123"
    assert argumentos["container_name"] == container_nome
    assert argumentos["blob_name"] == nome_blob
    assert argumentos["permission"].read is True

    # Verifica se o blob foi acessado
    azure_mock["service"].get_container_client.assert_called_once_with(
        container_nome
    )

    azure_mock["container"].get_blob_client.assert_called_once_with(
        nome_blob
    )

    # Verifica a URL retornada
    assert resultado.endswith("?token_ficticio")

    # Resultado esperado: URL SAS gerada corretamente, com os dados da conta, permissões de leitura e endereço do blob.


def test_gerar_url_sas_com_expiracao_personalizada(
    azure_mock,
    connection_string_mock
):
    with patch(
        "services.azure_storage_service.generate_blob_sas"
    ) as sas_mock:

        sas_mock.return_value = "token_ficticio"

        gerar_url_sas(
            "produtos",
            "produto_123.jpg",
            expiracao_minutos=30
        )

    argumentos = sas_mock.call_args.kwargs

    # Verifica se a expiração está aproximadamente correta
    diferenca = argumentos["expiry"] - datetime.now(timezone.utc)

    assert timedelta(minutes=29) < diferenca < timedelta(minutes=30)

    # Resultado esperado: token SAS configurado com expiração de aproximadamente 30 minutos.


def test_gerar_url_sas_sem_account_name(
    azure_mock,
    monkeypatch
):
    from services import azure_storage_service

    monkeypatch.setattr(
        azure_storage_service,
        "CONNECTION_STRING",
        "DefaultEndpointsProtocol=https;AccountKey=chaveficticia123;"
    )

    try:
        gerar_url_sas("produtos", "produto_123.jpg")
        assert False, "Era esperado RuntimeError"
    except RuntimeError as erro:
        assert "AccountName ou AccountKey" in str(erro)

    # Resultado esperado: RuntimeError informando que AccountName ou AccountKey não foram encontrados.


def test_gerar_url_sas_sem_account_key(
    azure_mock,
    monkeypatch
):
    from services import azure_storage_service

    monkeypatch.setattr(
        azure_storage_service,
        "CONNECTION_STRING",
        "DefaultEndpointsProtocol=https;AccountName=contateste;"
    )

    try:
        gerar_url_sas("produtos", "produto_123.jpg")
        assert False, "Era esperado RuntimeError"
    except RuntimeError as erro:
        assert "AccountName ou AccountKey" in str(erro)

    # Resultado esperado: RuntimeError informando que AccountName ou AccountKey não foram encontrados.
