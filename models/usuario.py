from models import db  # importa a instância do banco (SQLAlchemy)

class Usuario(db.Model):
    __tablename__ = 'usuarios'  
    # nome da tabela no banco de dados

    id = db.Column(db.Integer, primary_key=True) 
    nome = db.Column(db.String(100), nullable=False)  # (obrigatório)
    email = db.Column(db.String(120), unique=True, nullable=False)  # (não pode repetir)
    telefone = db.Column(db.String(20))  
    estado = db.Column(db.String(50))
    cidade = db.Column(db.String(50))
    senha = db.Column(db.String(200), nullable=False)  
    tipo = db.Column(db.String(20), nullable=False)  # 'produtor' ou 'estabelecimento' 
    avaliacao = db.Column(db.Float)  # média das avaliações recebidas

    # =========================
    # RELACIONAMENTOS
    # =========================

    produtos = db.relationship(
    'Produto', 
    backref='produtor', 
    lazy=True, 
    cascade="all, delete-orphan")  
    # Cria uma relação 1:N entre Usuario e Produto:
    # - Um usuário pode ter vários produtos → acesso via: usuario.produtos
    # - backref='produtor' cria o caminho inverso automaticamente,
    #   permitindo acessar o dono do produto assim: produto.produtor
    # - lazy=True faz com que os produtos só sejam carregados do banco
    #   quando forem acessados (carregamento sob demanda)

    negociacoes_como_comprador = db.relationship(
    'Negociacao',
    foreign_keys='Negociacao.comprador_id',
    backref='comprador',
    lazy=True,
    cascade="all, delete-orphan"
    )
    # Cria uma relação 1:N entre Usuario e Negociacao (como comprador):
    # - Um usuário pode ter várias negociações como comprador → acesso via:
    #   usuario.negociacoes_como_comprador
    #
    # - foreign_keys='Negociacao.comprador_id' especifica qual campo da tabela
    #   Negociacao será usado nessa relação (necessário porque existem dois
    #   vínculos com Usuario: comprador_id e vendedor_id)

    negociacoes_como_vendedor = db.relationship(
    'Negociacao',
    foreign_keys='Negociacao.vendedor_id',
    backref='vendedor',
    lazy=True,
    cascade="all, delete-orphan"
    )
    # Cria uma relação 1:N entre Usuario e Negociacao (como vendedor):
    # - Um usuário (produtor) pode ter várias negociações como vendedor → acesso via:
    #   usuario.negociacoes_como_vendedor
    #
    # - foreign_keys='Negociacao.vendedor_id' define qual campo da tabela Negociacao
    #   será usado nessa relação (necessário porque existem duas referências para Usuario:
    #   comprador_id e vendedor_id)