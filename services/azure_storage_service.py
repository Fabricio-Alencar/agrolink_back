import os
from datetime import datetime, timedelta, timezone

from azure.storage.blob import (
    BlobServiceClient,
    BlobSasPermissions,
    generate_blob_sas
)
from dotenv import load_dotenv

load_dotenv()

CONTAINER_PRODUTOS = "produtos"
CONTAINER_USUARIOS = "usuarios"

CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")

if not CONNECTION_STRING:
    raise RuntimeError(
        "AZURE_STORAGE_CONNECTION_STRING não foi definida nas variáveis de ambiente"
    )

blob_service_client = BlobServiceClient.from_connection_string(
    CONNECTION_STRING
)


def upload_arquivo(arquivo, nome_blob, container_nome):
    container_client = blob_service_client.get_container_client(
        container_nome
    )

    blob_client = container_client.get_blob_client(nome_blob)

    blob_client.upload_blob(
        arquivo,
        overwrite=True
    )

    return nome_blob


def gerar_url_sas(container_nome, nome_blob, expiracao_minutos=60):
    partes = {}

    for parte in CONNECTION_STRING.split(";"):
        if "=" in parte:
            chave, valor = parte.split("=", 1)
            partes[chave] = valor

    account_name = partes.get("AccountName")
    account_key = partes.get("AccountKey")

    if not account_name or not account_key:
        raise RuntimeError(
            "AccountName ou AccountKey não encontrados na connection string"
        )

    sas_token = generate_blob_sas(
        account_name=account_name,
        container_name=container_nome,
        blob_name=nome_blob,
        account_key=account_key,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.now(timezone.utc)
        + timedelta(minutes=expiracao_minutos)
    )

    blob_client = (
        blob_service_client
        .get_container_client(container_nome)
        .get_blob_client(nome_blob)
    )

    return f"{blob_client.url}?{sas_token}"

def deletar_arquivo(nome_blob, container_nome):
    if not nome_blob:
        return

    container_client = blob_service_client.get_container_client(
        container_nome
    )

    blob_client = container_client.get_blob_client(nome_blob)

    if blob_client.exists():
        blob_client.delete_blob()
        print(
            f"🗑️ Blob removido: {container_nome}/{nome_blob}"
        )
    else:
        print(
            f"⚠️ Blob não encontrado: {container_nome}/{nome_blob}"
        )    