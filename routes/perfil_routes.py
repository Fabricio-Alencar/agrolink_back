from fastapi import APIRouter, Depends, Form, UploadFile, File, HTTPException, status

from services import perfil_service
from auth.dependencies import get_current_user


router = APIRouter(tags=["Perfil"])


# =========================
# BUSCAR DADOS DO PERFIL (LOGADO)
# =========================
@router.get("/perfil")
def obter_perfil(usuario_logado=Depends(get_current_user)):
    # 1. PEGA O ID DO USUÁRIO LOGADO
    user_id = usuario_logado["user_id"]

    try:
        # 2. CHAMA O SERVICE
        usuario = perfil_service.obter_perfil_usuario(user_id)

        # 3. RETORNA DADOS FORMATADOS PARA O FRONT
        return {
            "nome": usuario.nome,
            "email": usuario.email,
            "telefone": usuario.telefone,
            "cidade": usuario.cidade,
            "estado": usuario.estado,
            "foto_perfil": getattr(usuario, "foto_perfil", "assets/user.webp"),
            "tipo": usuario.tipo
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# =========================
# ATUALIZAR PERFIL E FOTO (LOGADO)
# =========================
@router.post("/perfil")
def atualizar_perfil(
    usuario_logado=Depends(get_current_user),

    nome: str | None = Form(default=None),
    email: str | None = Form(default=None),
    telefone: str | None = Form(default=None),
    cidade: str | None = Form(default=None),
    estado: str | None = Form(default=None),
    senha: str | None = Form(default=None),

    foto: UploadFile | None = File(default=None)
):
    # 1. PEGA O ID DO USUÁRIO LOGADO
    user_id = usuario_logado["user_id"]

    # 2. MONTA OS DADOS DO FORMULÁRIO
    data = {
        "nome": nome,
        "email": email,
        "telefone": telefone,
        "cidade": cidade,
        "estado": estado,
        "senha": senha
    }

    try:
        # 3. CHAMA O SERVICE
        usuario = perfil_service.atualizar_perfil_usuario(
            user_id,
            data,
            foto
        )

        return {
            "msg": "Perfil atualizado com sucesso",
            "foto_perfil": getattr(
                usuario,
                "foto_perfil",
                "assets/user.webp"
            )
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# =========================
# EXCLUIR CONTA (LOGADO)
# =========================
@router.delete("/perfil")
def excluir_conta(usuario_logado=Depends(get_current_user)):
    # 1. PEGA O ID DO USUÁRIO LOGADO
    user_id = usuario_logado["user_id"]

    try:
        # 2. CHAMA O SERVICE
        perfil_service.excluir_conta_usuario(user_id)

        return {
            "msg": "Conta excluída com sucesso"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )