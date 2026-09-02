from models.produto import Produto
from models.negociacao import Negociacao
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from database import SessionLocal


def listar_produtos():
    db = SessionLocal()

    try:
        # Usamos joinedload para trazer os dados do produtor junto com o produto de uma vez só
        # o filter retorne apenas os produtos que estão "publicados" para aparecer no marketplace
        produtos = db.execute(
            select(Produto)
            .options(joinedload(Produto.produtor))
            .where(Produto.status == "publicado")
        ).scalars().all()

        return produtos

    finally:
        db.close()


def registrar_pedido(comprador_id, data):
    db = SessionLocal()

    try:
        # 1. Buscar o produto para validar e pegar o vendedor_id
        produto = db.get(Produto, data['produto_id'])

        if not produto:
            raise Exception("Produto não encontrado.")

        # 2. Converter string 'YYYY-MM-DD' para objeto Date do Python
        try:
            data_formatada = datetime.strptime(
                data['data_entrega'],
                '%Y-%m-%d'
            ).date()
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

        db.add(nova_negociacao)
        db.commit()
        db.refresh(nova_negociacao)

        return nova_negociacao

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()
