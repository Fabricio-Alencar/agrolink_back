
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.auth_routes import router as auth_router
from routes.perfil_routes import router as perfil_router
from routes.produtos_routes import router as produtos_router
from routes.marketplace_routes import router as marketplace_router
from routes.negociacoes_routes import router as negociacoes_router
from routes.chat_routes import router as chat_router
from routes.avaliacoes_routes import router as avaliacoes_router

from sqlalchemy import inspect, text

from database import engine

from chat_database import ChatBase
from models.mensagem import Mensagem
from models.conversa import Conversa
from models.avaliacao import Avaliacao


app = FastAPI(title="AgroLink API")


# =========================
# BANCO DO CHAT
# =========================

ChatBase.metadata.create_all(bind=engine)


# =========================
# TABELA DE AVALIAÇÕES
# =========================
# Cria só a tabela nova, se ainda não existir (não mexe nas outras)

Avaliacao.__table__.create(bind=engine, checkfirst=True)


# =========================
# COLUNA negociacoes.data_atualizacao
# =========================
# O projeto não usa migrations: se a coluna ainda não existir no banco,
# ela é adicionada aqui (só acrescenta, não apaga nada)

try:
    if "data_atualizacao" not in [
        coluna["name"] for coluna in inspect(engine).get_columns("negociacoes")
    ]:
        # IF NOT EXISTS (Postgres) evita erro se dois processos subirem juntos
        se_nao_existir = "IF NOT EXISTS " if engine.dialect.name == "postgresql" else ""

        with engine.begin() as conexao:
            conexao.execute(text(
                f"ALTER TABLE negociacoes ADD COLUMN {se_nao_existir}data_atualizacao TIMESTAMP"
            ))

        print("Coluna negociacoes.data_atualizacao criada.")

except Exception as e:
    print(f"[AVISO] Não foi possível criar negociacoes.data_atualizacao: {e}")


# =========================
# CONFIGURAÇÃO DO CORS
# =========================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://127.0.0.1:8000",
        "https://front-agrolink-aff0bvbqd2buhfax.eastus-01.azurewebsites.net",
        "https://back-agrolink-bmbkepbbdkabdhhd.eastus-01.azurewebsites.net",
        "https://agro-link.azurewebsites.net",
        "https://agrolink-h3h0amghctcne7ey.brazilsouth-01.azurewebsites.net",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================
# ROTAS
# =========================

app.include_router(auth_router)
app.include_router(perfil_router)
app.include_router(produtos_router)
app.include_router(marketplace_router)
app.include_router(negociacoes_router)
app.include_router(chat_router)
app.include_router(avaliacoes_router)


@app.get("/")
def root():

    return {
        "message": "AgroLink API funcionando!"
    }
