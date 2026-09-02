from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    Float,
    Date,
    Text,
    String,
    Boolean,
    DateTime,
    ForeignKey
)
from sqlalchemy.orm import relationship

from database import Base  # importa a classe base do SQLAlchemy


class Negociacao(Base):
    __tablename__ = 'negociacoes'

    id = Column(Integer, primary_key=True)

    produto_id = Column(
        Integer,
        ForeignKey('produtos.id'),
        nullable=False
    )

    comprador_id = Column(
        Integer,
        ForeignKey('usuarios.id'),
        nullable=False
    )

    vendedor_id = Column(
        Integer,
        ForeignKey('usuarios.id'),
        nullable=False
    )

    quantidade = Column(Float, nullable=False)

    data_entrega = Column(Date)

    descricao = Column(Text)

    status = Column(String(20), default='pendente')
    # pendente | aceito | recusado | finalizado

    entrega_confirmada = Column(Boolean, default=False)
    recebimento_confirmado = Column(Boolean, default=False)

    oculto_comprador = Column(Boolean, default=False)
    oculto_vendedor = Column(Boolean, default=False)

    data_criacao = Column(
        DateTime,
        default=datetime.utcnow
    )

    # =========================
    # RELACIONAMENTOS
    # =========================

    produto = relationship(
        'Produto',
        back_populates='negociacoes'
    )
    # Cria o relacionamento entre Negociacao e Produto:
    # - Uma negociação pertence a um produto → acesso via:
    #   negociacao.produto
    # - back_populates='negociacoes' cria o caminho inverso,
    #   permitindo acessar as negociações de um produto via:
    #   produto.negociacoes

    comprador = relationship(
        'Usuario',
        foreign_keys=[comprador_id],
        back_populates='negociacoes_como_comprador'
    )
    # Cria o relacionamento entre Negociacao e Usuario (como comprador):
    # - Uma negociação possui um comprador → acesso via:
    #   negociacao.comprador
    #
    # - foreign_keys=[comprador_id] especifica que comprador_id
    #   será utilizado para relacionar a negociação ao Usuario.
    #   Isso é necessário porque existem dois vínculos com Usuario:
    #   comprador_id e vendedor_id.

    vendedor = relationship(
        'Usuario',
        foreign_keys=[vendedor_id],
        back_populates='negociacoes_como_vendedor'
    )
    # Cria o relacionamento entre Negociacao e Usuario (como vendedor):
    # - Uma negociação possui um vendedor → acesso via:
    #   negociacao.vendedor
    #
    # - foreign_keys=[vendedor_id] especifica que vendedor_id
    #   será utilizado para relacionar a negociação ao Usuario.
    #   Isso é necessário porque existem duas referências para Usuario:
    #   comprador_id e vendedor_id.