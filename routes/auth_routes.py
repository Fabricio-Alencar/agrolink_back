from fastapi import APIRouter, Response, Depends, status
from fastapi.responses import JSONResponse

from services.usuario_service import criar_usuario, login_usuario
from services.perfil_service import obter_perfil_usuario
from services.azure_storage_service import (
    gerar_url_sas,
    CONTAINER_USUARIOS
)

from auth.security import criar_token
from auth.dependencies import get_current_user


router = APIRouter(tags=["Autenticação"])


# =========================
# CADASTRO
# =========================
@router.post("/cadastro", status_code=status.HTTP_201_CREATED)
def cadastro(data: dict):
    try:
        usuario = criar_usuario(data)

        return {
            "msg": "Login realizado",
            "user": {
                "id": usuario.id,
                "nome": usuario.nome,
                "tipo": usuario.tipo
            }
        }

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "erro": str(e)
            }
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
            key="access_token",
            value=token,
            httponly=True,
            secure=True,
            samesite="none",
            max_age=60 * 60 * 24
        )

        return {
            "msg": "Login realizado",
            "user": {
                "id": usuario.id,
                "nome": usuario.nome,
                "tipo": usuario.tipo
            }
        }

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "erro": str(e)
            }
        )


# =========================
# SESSÃO
# =========================
@router.get("/session")
def get_session(usuario=Depends(get_current_user)):

    try:
        # ID do usuário que está no JWT
        user_id = usuario["user_id"]

        # Busca o usuário completo no banco
        usuario_banco = obter_perfil_usuario(user_id)

        if not usuario_banco:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "erro": "Usuário não encontrado"
                }
            )

        # ==========================================
        # FOTO DE PERFIL
        # ==========================================

        foto_perfil = getattr(
            usuario_banco,
            "foto_perfil",
            None
        )

        if foto_perfil and "user.webp" not in foto_perfil:

            # Se já for uma URL, mantém
            if (
                foto_perfil.startswith("http://")
                or foto_perfil.startswith("https://")
            ):
                pass

            # Caso seja apenas o nome do Blob,
            # gera uma URL SAS
            else:
                foto_perfil = gerar_url_sas(
                    CONTAINER_USUARIOS,
                    foto_perfil
                )

        else:
            foto_perfil = None


        # ==========================================
        # RESPOSTA
        # ==========================================

        return {
            "logado": True,
            "user_id": usuario_banco.id,
            "tipo": usuario_banco.tipo,
            "nome": usuario_banco.nome,
            "foto_perfil": foto_perfil
        }

    except Exception as e:

        print("❌ Erro ao carregar /session:", str(e))

        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "erro": str(e)
            }
        )