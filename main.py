from fastapi import FastAPI

from routes.auth_routes import router as auth_router
from routes.perfil_routes import router as perfil_router
from routes.produtos_routes import router as produtos_router
from routes.marketplace_routes import router as marketplace_router
from routes.negociacoes_routes import router as negociacoes_router

app = FastAPI(title="AgroLink API")


# =========================
# ROTAS
# =========================

app.include_router(auth_router)
app.include_router(perfil_router)
app.include_router(produtos_router)
app.include_router(marketplace_router)
app.include_router(negociacoes_router)


@app.get("/")
def root():
    return {"message": "AgroLink API funcionando!"}