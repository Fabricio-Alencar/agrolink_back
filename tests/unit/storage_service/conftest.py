
import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def azure_mock():
    """Simula o cliente do Azure Blob Storage."""

    with patch("services.azure_storage_service.blob_service_client") as mock:
        container_mock = MagicMock()
        blob_mock = MagicMock()

        mock.get_container_client.return_value = container_mock
        container_mock.get_blob_client.return_value = blob_mock

        yield {
            "service": mock,
            "container": container_mock,
            "blob": blob_mock
        }


@pytest.fixture
def connection_string_mock(monkeypatch):
    """Fornece uma connection string fictícia."""

    from services import azure_storage_service

    connection_string = (
        "DefaultEndpointsProtocol=https;"
        "AccountName=contateste;"
        "AccountKey=chaveficticia123;"
        "EndpointSuffix=core.windows.net"
    )

    monkeypatch.setattr(
        azure_storage_service,
        "CONNECTION_STRING",
        connection_string
    )

    return connection_string
