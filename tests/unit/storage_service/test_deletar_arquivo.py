
from services.azure_storage_service import deletar_arquivo


def test_deletar_arquivo_com_sucesso(azure_mock):
    nome_blob = "produto_123.jpg"
    container_nome = "produtos"

    azure_mock["blob"].exists.return_value = True

    resultado = deletar_arquivo(
        nome_blob,
        container_nome
    )

    # Verifica se o container utilizado é o correto
    azure_mock["service"].get_container_client.assert_called_once_with(
        container_nome
    )

    # Verifica se o blob utilizado é o correto
    azure_mock["container"].get_blob_client.assert_called_once_with(
        nome_blob
    )

    # Verifica se a existência do arquivo foi verificada
    azure_mock["blob"].exists.assert_called_once()

    # Verifica se o arquivo foi excluído
    azure_mock["blob"].delete_blob.assert_called_once()

    # Resultado esperado: arquivo existente excluído do container correto.


def test_deletar_arquivo_inexistente(azure_mock):
    nome_blob = "produto_inexistente.jpg"

    azure_mock["blob"].exists.return_value = False

    resultado = deletar_arquivo(
        nome_blob,
        "produtos"
    )

    # Verifica se a existência do arquivo foi consultada
    azure_mock["blob"].exists.assert_called_once()

    # Verifica se a exclusão não foi executada
    azure_mock["blob"].delete_blob.assert_not_called()

    # Resultado esperado: nenhuma exclusão realizada quando o arquivo não existe.


def test_deletar_arquivo_com_nome_vazio(azure_mock):
    resultado = deletar_arquivo(
        "",
        "produtos"
    )

    # Verifica se nenhuma operação no Azure foi realizada
    azure_mock["service"].get_container_client.assert_not_called()

    # Resultado esperado: função encerrada sem acessar o Azure quando o nome do blob está vazio.


def test_deletar_arquivo_com_nome_none(azure_mock):
    resultado = deletar_arquivo(
        None,
        "produtos"
    )

    # Verifica se nenhuma operação no Azure foi realizada
    azure_mock["service"].get_container_client.assert_not_called()

    # Resultado esperado: função encerrada sem acessar o Azure quando o nome do blob é None.
