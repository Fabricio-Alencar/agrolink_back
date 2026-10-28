from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    DateTime
)

from chat_database import ChatBase


class Conversa(ChatBase):

    __tablename__ = "conversas"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    negociacao_id = Column(
        Integer,
        nullable=False,
        unique=True,
        index=True
    )

    iniciada_por_id = Column(
        Integer,
        nullable=False
    )

    data_criacao = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )