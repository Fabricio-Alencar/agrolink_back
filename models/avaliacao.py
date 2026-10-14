from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    Float,
    Text,
    DateTime,
    ForeignKey
)
from sqlalchemy.orm import relationship

from database import Base  # importa a classe base do SQLAlchemy


class Avaliacao(Base):
    __tablename__ = 'avaliacoes'

    id = Column(Integer, primary_key=True)

    # Uma avaliação por negociação.
    # ondelete='SET NULL' mantém a nota do produtor mesmo quando a negociação
    # é apagada de vez do banco (quando os dois lados ocultam o histórico)
    negociacao_id = Column(
        Integer,
        ForeignKey('negociacoes.id', ondelete='SET NULL'),
        unique=True,
        nullable=True
    )

    # Estabelecimento que deu a nota
    avaliador_id = Column(
        Integer,
        ForeignKey('usuarios.id', ondelete='CASCADE'),
        nullable=False
    )

    # Produtor que recebeu a nota
    avaliado_id = Column(
        Integer,
        ForeignKey('usuarios.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    nota = Column(Float, nullable=False)  # de 0.5 a 5, de meia em meia estrela

    comentario = Column(Text)  # opcional

    data_criacao = Column(
        DateTime,
        default=datetime.utcnow
    )

    # =========================
    # RELACIONAMENTOS
    # =========================

    avaliador = relationship('Usuario', foreign_keys=[avaliador_id])
    # Permite mostrar o nome do estabelecimento na lista de avaliações:
    #   avaliacao.avaliador.nome
