import json
import time
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from database import SessionLocal
from models.produto import Produto
from models.negociacao import Negociacao
from services.cache_service import redis_client

CACHE_KEY = "marketplace"
CACHE_TTL = 60


def listar_produtos():
    inicio_total = time.perf_counter()

    inicio_redis = time.perf_counter()
    dados_cache = redis_client.get(CACHE_KEY)
    fim_redis = time.perf_counter()
    tempo_redis = (fim_redis - inicio_redis) * 1000

    print(f"Tempo da busca no Redis: {tempo_redis:.2f} ms")

    if dados_cache:
        print("Marketplace: dados encontrados no Redis.")
        fim_total = time.perf_counter()
        print(f"Tempo total da busca no Marketplace: {(fim_total - inicio_total) * 1000:.2f} ms")
        return json.loads(dados_cache)

    print("Marketplace: cache vazio. Buscando no PostgreSQL.")
    db = SessionLocal()

    try:
        inicio_postgres = time.perf_counter()
        produtos = db.execute(
            select(Produto)
            .options(joinedload(Produto.produtor))
            .where(Produto.status == "publicado")
        ).scalars().all()
        fim_postgres = time.perf_counter()

        tempo_postgres = (fim_postgres - inicio_postgres) * 1000
        print(f"Tempo da busca no PostgreSQL: {tempo_postgres:.2f} ms")

        dados_produtos = [
            {
                "id": p.id,
                "nome": p.nome,
                "preco": float(p.preco) if p.preco is not None else None,
                "quantidade": float(p.quantidade) if p.quantidade is not None else None,
                "unidade": p.unidade,
                "categoria": p.categoria,
                "descricao": p.descricao,
                "foto": p.foto,
                "status": p.status,
                "produtor_nome": p.produtor.nome,
                "produtor_estado": p.produtor.estado,
                "produtor_cidade": p.produtor.cidade,
                "produtor_avaliacao": p.produtor.avaliacao or 5.0
            }
            for p in produtos
        ]

        redis_client.set(CACHE_KEY, json.dumps(dados_produtos), ex=CACHE_TTL)
        print("Marketplace: dados salvos no Redis.")

        fim_total = time.perf_counter()
        print(f"Tempo total da busca no Marketplace: {(fim_total - inicio_total) * 1000:.2f} ms")

        return dados_produtos
    finally:
        db.close()


def registrar_pedido(comprador_id, data):
    db = SessionLocal()
    try:
        produto = db.get(Produto, data['produto_id'])

        if not produto:
            raise Exception("Produto não encontrado.")

        try:
            data_formatada = datetime.strptime(data['data_entrega'], '%Y-%m-%d').date()
        except (ValueError, KeyError):
            data_formatada = None

        nova_negociacao = Negociacao(
            produto_id=produto.id,
            vendedor_id=produto.produtor_id,
            comprador_id=comprador_id,
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