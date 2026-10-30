import os
from unittest.mock import patch

import pytest

os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("REDIS_PASSWORD", "senha_ficticia")


@pytest.fixture
def redis_mock():
    """Simula o cliente Redis."""

    with patch("services.cache_service.redis_client") as mock:
        yield mock