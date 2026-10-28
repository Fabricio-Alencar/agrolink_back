from sqlalchemy.orm import DeclarativeBase

from database import engine, SessionLocal


# =========================================================
# BANCO DO CHAT
# =========================================================

class ChatBase(DeclarativeBase):
    pass


# Utiliza a mesma sessão do banco principal.
SessionChat = SessionLocal


def get_chat_db():

    db = SessionChat()

    try:

        yield db

    finally:

        db.close()