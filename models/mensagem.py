
from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    Text,
    DateTime,
    Boolean
)

from chat_database import ChatBase


class Mensagem(ChatBase):
    __tablename__ = "mensagens"

    id = Column(
        Integer,
        primary_key=True
    )

    negociacao_id = Column(
        Integer,
        nullable=False
    )

    remetente_id = Column(
        Integer,
        nullable=False
    )

    texto = Column(
        Text,
        nullable=False
    )

    data_envio = Column(
        DateTime,
        default=datetime.utcnow
    )

    lida = Column(
        Boolean,
        default=False
    )
