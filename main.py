from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.auth_routes import router as auth_router
from routes.perfil_routes import router as perfil_router
from routes.produtos_routes import router as produtos_router
from routes.marketplace_routes import router as marketplace_router
from routes.negociacoes_routes import router as negociacoes_router

app = FastAPI(title="AgroLink API")

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
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(perfil_router)
app.include_router(produtos_router)
app.include_router(marketplace_router)
app.include_router(negociacoes_router)


@app.get("/")
def root():
    return {"message": "AgroLink API funcionando!"}
