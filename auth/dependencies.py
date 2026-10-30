
from fastapi import Cookie, HTTPException, status

from database import SessionLocal
from models.usuario import Usuario

from auth.security import decodificar_token


# =========================
# BUSCAR USUÁRIO LOGADO
# =========================
def get_current_user(
    access_token: str | None = Cookie(default=None)
):
    # Verifica se existe um token no cookie
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não autenticado"
        )

    try:
        # Decodifica e valida o JWT
        payload = decodificar_token(access_token)

        user_id = payload.get("sub")
        tipo = payload.get("tipo")

        # Verifica se o token possui os dados necessários
        if not user_id or not tipo:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido"
            )

        # =========================
        # BUSCA DO USUÁRIO NO BANCO
        # =========================
        db = SessionLocal()

        try:
            usuario = db.get(
                Usuario,
                int(user_id)
            )

            # Conta excluída não pode mais usar o sistema
            if not usuario or getattr(usuario, "conta_excluida", False) is True:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Usuário não encontrado"
                )

            return {
                "user_id": usuario.id,
                "tipo": usuario.tipo,
                "nome": usuario.nome
            }

        finally:
            db.close()

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado"
        )
