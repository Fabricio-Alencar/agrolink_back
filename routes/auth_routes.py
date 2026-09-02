from fastapi import APIRouter, Response, HTTPException, Depends, status

from services.usuario_service import criar_usuario, login_usuario
from auth.security import criar_token
from auth.dependencies import get_current_user


router = APIRouter(tags=["Autenticação"])


@router.post("/cadastro", status_code=status.HTTP_201_CREATED)
def cadastro(data: dict):
    try:
        usuario = criar_usuario(data)

        # Retornamos sucesso. O JS lerá isso e fará o redirecionamento.
        return {
            "msg": "Usuário criado com sucesso",
            "proxima_pagina": "/login"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# =========================
# LOGIN
# =========================
@router.post("/login")
def login(data: dict, response: Response):
    try:
        usuario = login_usuario(data)

        # Cria o token JWT
        token = criar_token(
            usuario.id,
            usuario.tipo
        )

        # Salva o JWT em um cookie HttpOnly
        response.set_cookie(
            key="access_token",        # Nome do cookie
            value=token,               # JWT
            httponly=True,             # Bloqueia acesso via JS
            secure=True,               # Apenas HTTPS
            samesite="none",           # Permite requisições entre origens
            max_age=60 * 60 * 24       # Expira em 24 horas
        )

        return {
            "msg": "Login realizado",
            "user_id": usuario.id,
            "tipo": usuario.tipo
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


# =========================
# SESSÃO
# =========================
@router.get("/session")
def get_session(usuario=Depends(get_current_user)):
    return {
        "logado": True,
        "user_id": usuario["user_id"],
        "tipo": usuario["tipo"],
        "nome": usuario["nome"]
    }
