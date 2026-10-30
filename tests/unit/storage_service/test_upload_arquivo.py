
from services.azure_storage_service import upload_arquivo

def test_upload_arquivo_com_sucesso(azure_mock):
    arquivo = b"conteudo ficticio da imagem"
    nome_blob = "produto_123.jpg"
    container_nome = "produtos"

    resultado = upload_arquivo(
        arquivo,
        nome_blob,
        container_nome
    )

    # Verifica o container utilizado
    azure_mock["service"].get_container_client.assert_called_once_with(
        container_nome
    )

    # Verifica o blob utilizado
    azure_mock["container"].get_blob_client.assert_called_once_with(
        nome_blob
    )

    # Verifica se o upload foi executado corretamente
    azure_mock["blob"].upload_blob.assert_called_once_with(
        arquivo,
        overwrite=True
    )

    # Verifica o retorno
    assert resultado == nome_blob


def test_upload_arquivo_sobrescreve_arquivo_existente(azure_mock):
    arquivo = b"novo conteudo"
    nome_blob = "produto_123.jpg"

    upload_arquivo(
        arquivo,
        nome_blob,
        "produtos"
    )

    # Confirma que a sobrescrita está ativada
    chamada = azure_mock["blob"].upload_blob.call_args

    assert chamada.kwargs["overwrite"] is True
