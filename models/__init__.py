from flask_sqlalchemy import SQLAlchemy
# SQLAlchemy é uma biblioteca que permite usar Python para criar e manipular o banco de dados.
# Ele transforma tabelas em classes e registros em objetos,
# evitando a necessidade de escrever SQL manualmente.


# instancia do banco
db = SQLAlchemy()

# isso garante que o SQLAlchemy conheça todas as tabelas

from .usuario import Usuario
from .produto import Produto
from .negociacao import Negociacao
