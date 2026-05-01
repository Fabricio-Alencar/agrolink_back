from models.produto import Produto 
from models.negociacao import Negociacao
from models import db
from datetime import datetime
from sqlalchemy.orm import joinedload


def listar_produtos():
    # Usamos joinedload para trazer os dados do produtor junto com o produto de uma vez só
    # o filter retorne apenas os produtos que estão "publicados" para aparecer no marketplace
    produtos = Produto.query.options(
        joinedload(Produto.produtor)
    ).filter((Produto.status) == "publicado").all()

    return produtos



def registrar_pedido(comprador_id, data):
    # 1. Buscar o produto para validar e pegar o vendedor_id
    produto = Produto.query.get(data['produto_id'])
    
    if not produto:
        raise Exception("Produto não encontrado.")

    # 2. Converter string 'YYYY-MM-DD' para objeto Date do Python
    try:
        data_formatada = datetime.strptime(data['data_entrega'], '%Y-%m-%d').date()
    except (ValueError, KeyError):
        data_formatada = None

    # 3. Criar a instância da Negociação
    nova_negociacao = Negociacao(
        produto_id=produto.id,
        vendedor_id=produto.produtor_id, # Pegamos o dono do produto
        comprador_id=comprador_id,       # Usuário logado
        quantidade=float(data['quantidade']),
        data_entrega=data_formatada,
        descricao=data.get('descricao'),
        status='pendente' 
    )

    db.session.add(nova_negociacao)
    db.session.commit()

    return nova_negociacao
    