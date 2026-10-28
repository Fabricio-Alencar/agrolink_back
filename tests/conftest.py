
import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault(
    "AZURE_STORAGE_CONNECTION_STRING",
    "UseDevelopmentStorage=true"
)
