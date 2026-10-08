from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.auth_routes import router as auth_router
from routes.perfil_routes import router as perfil_router
from routes.produtos_routes import router as produtos_router
from routes.marketplace_routes import router as marketplace_router
from routes.negociacoes_routes import router as negociacoes_router
from routes.chat_routes import router as chat_router

from database import engine

from chat_database import ChatBase
from models.mensagem import Mensagem


app = FastAPI(title="AgroLink API")


# =========================
# BANCO DO CHAT
# =========================

ChatBase.metadata.create_all(bind=engine)


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


@app.get("/")
def root():
    return {"message": "AgroLink API funcionando!"}