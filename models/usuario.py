from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import relationship

from database import Base  # importa a classe base do SQLAlchemy


class Usuario(Base):
    __tablename__ = 'usuarios'
    # nome da tabela no banco de dados

    id = Column(Integer, primary_key=True)
    nome = Column(String(100), nullable=False)  # (obrigatório)
    email = Column(String(120), unique=True, nullable=False)  # (não pode repetir)
    telefone = Column(String(20))
    estado = Column(String(50))
    cidade = Column(String(50))
    senha = Column(String(200), nullable=False)
    tipo = Column(String(20), nullable=False)  # 'produtor' ou 'estabelecimento'
    avaliacao = Column(Float)  # média das avaliações recebidas
    foto_perfil = Column(
        String(255),
        default='static/uploads/perfis/user.webp'
    )

    # =========================
    # RELACIONAMENTOS
    # =========================

    produtos = relationship(
        'Produto',
        back_populates='produtor',
        cascade="all, delete-orphan"
    )
    # Cria uma relação 1:N entre Usuario e Produto:
    # - Um usuário pode ter vários produtos → acesso via: usuario.produtos
    # - back_populates='produtor' cria o caminho inverso,
    #   permitindo acessar o dono do produto assim: produto.produtor
    # - O relacionamento é carregado pelo SQLAlchemy quando for acessado.

    negociacoes_como_comprador = relationship(
        'Negociacao',
        foreign_keys='Negociacao.comprador_id',
        back_populates='comprador'
    )
    # Cria uma relação 1:N entre Usuario e Negociacao (como comprador):
    # - Um usuário pode ter várias negociações como comprador → acesso via:
    #   usuario.negociacoes_como_comprador
    #
    # - foreign_keys='Negociacao.comprador_id' especifica qual campo da tabela
    #   Negociacao será usado nessa relação (necessário porque existem dois
    #   vínculos com Usuario: comprador_id e vendedor_id)

    negociacoes_como_vendedor = relationship(
        'Negociacao',
        foreign_keys='Negociacao.vendedor_id',
        back_populates='vendedor'
    )
    # Cria uma relação 1:N entre Usuario e Negociacao (como vendedor):
    # - Um usuário (produtor) pode ter várias negociações como vendedor → acesso via:
    #   usuario.negociacoes_como_vendedor
    #
    # - foreign_keys='Negociacao.vendedor_id' define qual campo da tabela Negociacao
    #   será usado nessa relação (necessário porque existem duas referências para Usuario:
    #   comprador_id e vendedor_id)