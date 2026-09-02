import os
from datetime import datetime, timedelta, timezone

import jwt
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY não foi definida no .env")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

# =========================
# CRIAR TOKEN JWT
# =========================
def criar_token(user_id, tipo):
    agora = datetime.now(timezone.utc)

    payload = {
        "sub": str(user_id),
        "tipo": tipo,
        "exp": agora + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


# =========================
# DECODIFICAR TOKEN JWT
# =========================
def decodificar_token(token):
    return jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[ALGORITHM]
    )
