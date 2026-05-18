import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = 'sua-chave-secreta-aqui'

    # =========================
    # POSTGRESQL AZURE
    # =========================
    SQLALCHEMY_DATABASE_URI = (
        "postgresql://adminagrolink:+Ravy123@agrolink.postgres.database.azure.com:5432/postgres?sslmode=require"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
