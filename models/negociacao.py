from models import db
from datetime import datetime

class Negociacao(db.Model):
    __tablename__ = 'negociacoes'

    id = db.Column(db.Integer, primary_key=True)

    produto_id = db.Column(
        db.Integer,
        db.ForeignKey('produtos.id'),
        nullable=False
    )

    comprador_id = db.Column(
        db.Integer,
        db.ForeignKey('usuarios.id'),
        nullable=False
    )

    vendedor_id = db.Column(
        db.Integer,
        db.ForeignKey('usuarios.id'),
        nullable=False
    )

    quantidade = db.Column(db.Float, nullable=False)

    data_entrega = db.Column(db.Date)

    descricao = db.Column(db.Text)

    status = db.Column(db.String(20), default='pendente')
    # pendente | aceito | recusado | finalizado

    entrega_confirmada = db.Column(db.Boolean, default=False)
    recebimento_confirmado = db.Column(db.Boolean, default=False)

    oculto_comprador = db.Column(db.Boolean, default=False)
    oculto_vendedor = db.Column(db.Boolean, default=False)

    data_criacao = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )