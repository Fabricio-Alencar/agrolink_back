import time

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
    inicio = time.perf_counter()

    # Verifica se existe um token no cookie
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não autenticado"
        )

    try:
        # Decodifica e valida o JWT
        inicio_jwt = time.perf_counter()

        payload = decodificar_token(access_token)

        fim_jwt = time.perf_counter()

        print(
            f"Tempo para decodificar JWT: "
            f"{(fim_jwt - inicio_jwt) * 1000:.2f} ms"
        )

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

        inicio_banco = time.perf_counter()

        db = SessionLocal()

        try:
            usuario = db.get(
                Usuario,
                int(user_id)
            )

            if not usuario:
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

            fim_banco = time.perf_counter()

            print(
                f"Tempo da busca do usuário no banco: "
                f"{(fim_banco - inicio_banco) * 1000:.2f} ms"
            )

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado"
        )

    finally:
        fim = time.perf_counter()

        print(
            f"Tempo total do get_current_user: "
            f"{(fim - inicio) * 1000:.2f} ms"
        )