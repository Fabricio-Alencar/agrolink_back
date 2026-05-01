import os  # biblioteca para lidar com caminhos de arquivos

# pega o caminho absoluto da pasta do projeto
BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # chave secreta usada pelo Flask (sessão, segurança, etc.)
    SECRET_KEY = 'sua-chave-secreta-aqui'

    # define o caminho do banco de dados SQLite
    # cria um arquivo chamado database.db dentro da pasta instance/
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'instance/database.db')

    # desativa rastreamento de modificações (economiza memória)
    SQLALCHEMY_TRACK_MODIFICATIONS = False