from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey
from sqlalchemy.orm import relationship

from database import Base  # importa a classe base do SQLAlchemy


class Produto(Base):
    __tablename__ = 'produtos'

    id = Column(Integer, primary_key=True)

    nome = Column(String(100), nullable=False)
    foto = Column(String(200))  # caminho da imagem
    categoria = Column(String(50))

    preco = Column(Float, nullable=False)
    unidade = Column(String(50))
    quantidade = Column(Float)
    descricao = Column(Text)
    status = Column(String(20))

    produtor_id = Column(
        Integer,
        ForeignKey('usuarios.id'),
        nullable=False
    )

    # RELACIONAMENTO

    produtor = relationship(
        'Usuario',
        back_populates='produtos'
    )
    # Cria o relacionamento entre Produto e Usuario:
    # - Um produto pertence a um produtor → acesso via: produto.produtor
    # - back_populates='produtos' cria o caminho inverso,
    #   permitindo acessar os produtos do usuário via: usuario.produtos

    negociacoes = relationship(
        'Negociacao',
        back_populates='produto',
        cascade="all, delete-orphan"
    )
    # Cria uma relação 1:N entre Produto e Negociacao:
    # - Um produto pode ter várias negociações → acesso via:
    #   produto.negociacoes
    #
    # - back_populates='produto' cria o caminho inverso,
    #   permitindo acessar o produto de uma negociação via:
    #   negociacao.produto
    #
    # - cascade="all, delete-orphan" significa que, se um produto
    #   for excluído, suas negociações relacionadas também serão excluídas.