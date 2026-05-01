from models import db

class Produto(db.Model):
    __tablename__ = 'produtos'

    id = db.Column(db.Integer, primary_key=True)

    nome = db.Column(db.String(100), nullable=False)
    foto = db.Column(db.String(200))  # caminho da imagem
    categoria = db.Column(db.String(50))

    preco = db.Column(db.Float, nullable=False)
    unidade = db.Column(db.String(50))  
    quantidade = db.Column(db.Float)
    descricao = db.Column(db.Text)
    status= db.Column(db.String(20)) 

    produtor_id = db.Column(
        db.Integer,
        db.ForeignKey('usuarios.id'),
        nullable=False
    )

    # RELACIONAMENTO
    negociacoes = db.relationship('Negociacao', 
                                  backref='produto', 
                                  lazy=True,
                                  cascade="all, delete-orphan"
    )
