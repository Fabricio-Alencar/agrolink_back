import os
import uuid

from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient

load_dotenv()

CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
CONTAINER_NAME = os.getenv("AZURE_CONTAINER")


def upload_imagem_azure(arquivo):
    """
    Faz upload da imagem para Azure Blob Storage
    e retorna a URL pública da imagem.
    """

    # conexão com Azure
    blob_service_client = BlobServiceClient.from_connection_string(
        CONNECTION_STRING
    )

    # extensão da imagem
    extensao = arquivo.filename.split(".")[-1]

    # nome único
    nome_arquivo = f"{uuid.uuid4()}.{extensao}"

    # cliente blob
    blob_client = blob_service_client.get_blob_client(
        container=CONTAINER_NAME,
        blob=nome_arquivo
    )

    # upload
    blob_client.upload_blob(
        arquivo,
        overwrite=True
    )

    # URL pública
    return blob_client.url
