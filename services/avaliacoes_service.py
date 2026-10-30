from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.orm import joinedload

from database import SessionLocal
from models import Usuario, Produto, Negociacao, Avaliacao
from models.usuario import nome_para_exibir
from services.cache_service import redis_client


NOTA_MINIMA = 0.5
NOTA_MAXIMA = 5
TAMANHO_MAXIMO_COMENTARIO = 500


# =========================
# RESUMO DAS AVALIAÇÕES (MÉDIA E QUANTIDADE)
# =========================
def resumo_avaliacoes(db, produtores_ids):
    """
    Retorna {produtor_id: {"media": 4.5, "total": 12}} só para quem tem avaliações.
    Produtor sem avaliações não aparece no dicionário (= "Sem avaliações").
    A média é sempre calculada pelas notas reais da tabela avaliacoes,
    ignorando o 5.0 que era gravado automaticamente no cadastro.
    """
    if not produtores_ids:
        return {}

    linhas = db.execute(
        select(
            Avaliacao.avaliado_id,
            func.avg(Avaliacao.nota),
            func.count(Avaliacao.id)
        )
        .where(Avaliacao.avaliado_id.in_(set(produtores_ids)))
        .group_by(Avaliacao.avaliado_id)
    ).all()

    return {
        produtor_id: {"media": round(float(media), 1), "total": total}
        for produtor_id, media, total in linhas
    }


# =========================
# NOTAS JÁ DADAS EM UMA LISTA DE NEGOCIAÇÕES
# =========================
def avaliacoes_das_negociacoes(db, negociacoes_ids):
    """Retorna {negociacao_id: Avaliacao} para saber quais pedidos já foram avaliados."""
    if not negociacoes_ids:
        return {}

    avaliacoes = db.execute(
        select(Avaliacao).where(Avaliacao.negociacao_id.in_(negociacoes_ids))
    ).scalars().all()

    return {a.negociacao_id: a for a in avaliacoes}


def avaliacao_para_json(avaliacao):
    if not avaliacao:
        return None

    return {
        "nota": avaliacao.nota,
        "comentario": avaliacao.comentario,
        "data": avaliacao.data_criacao.isoformat() if avaliacao.data_criacao else None
    }


# =========================
# AVALIAR PRODUTOR
# =========================
def avaliar_produtor(negociacao_id, user_id, nota, comentario=None):
    db = SessionLocal()

    try:
        negociacao = db.get(Negociacao, negociacao_id)

        if not negociacao:
            return {"erro": "Negociação não encontrada"}, 404

        # Só o estabelecimento que comprou pode avaliar o produtor
        if negociacao.comprador_id != user_id:
            return {"erro": "Apenas o estabelecimento desta negociação pode avaliar"}, 403

        if (negociacao.status or "").lower() != "finalizado":
            return {"erro": "A negociação precisa estar finalizada para ser avaliada"}, 400

        # Nota de 0.5 a 5, de meia em meia estrela (bool é barrado separadamente)
        if (
            isinstance(nota, bool)
            or not isinstance(nota, (int, float))
            or not NOTA_MINIMA <= nota <= NOTA_MAXIMA
            or (nota * 2) != int(nota * 2)
        ):
            return {"erro": "A nota deve ser de 0,5 a 5, de meia em meia estrela"}, 400

        if comentario is not None and not isinstance(comentario, str):
            return {"erro": "Comentário inválido"}, 400

        comentario = (comentario or "").strip() or None

        if comentario and len(comentario) > TAMANHO_MAXIMO_COMENTARIO:
            return {"erro": f"O comentário pode ter no máximo {TAMANHO_MAXIMO_COMENTARIO} caracteres"}, 400

        # Avaliação registrada não pode ser alterada
        ja_avaliada = db.execute(
            select(Avaliacao.id).where(Avaliacao.negociacao_id == negociacao.id)
        ).first()

        if ja_avaliada:
            return {"erro": "Esta negociação já foi avaliada"}, 409

        db.add(Avaliacao(
            negociacao_id=negociacao.id,
            avaliador_id=user_id,
            avaliado_id=negociacao.vendedor_id,
            nota=float(nota),
            comentario=comentario
        ))
        # Avaliar também conta como atualização: o pedido sobe na lista do produtor
        negociacao.data_atualizacao = datetime.utcnow()
        db.flush()

        # Mantém a coluna usuarios.avaliacao atualizada com a média real
        resumo = resumo_avaliacoes(db, [negociacao.vendedor_id])[negociacao.vendedor_id]
        db.get(Usuario, negociacao.vendedor_id).avaliacao = resumo["media"]

        db.commit()

        # A média aparece no marketplace, então o cache precisa ser renovado
        try:
            redis_client.delete("marketplace")
        except Exception as e:
            print(f"[AVISO] Não foi possível limpar o cache do marketplace: {e}")

        return {
            "mensagem": "Avaliação registrada com sucesso",
            "nota": float(nota),
            "media_produtor": resumo["media"],
            "total_avaliacoes": resumo["total"]
        }, 200

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


# =========================
# PERFIL PÚBLICO DO PRODUTOR
# =========================
def perfil_publico_produtor(produtor_id):
    db = SessionLocal()

    try:
        produtor = db.get(Usuario, produtor_id)

        if not produtor or produtor.tipo != "produtor":
            return None

        resumo = resumo_avaliacoes(db, [produtor.id]).get(produtor.id)

        # Quantas avaliações existem de cada nota (para as barrinhas do perfil)
        distribuicao = {str(n / 2): 0 for n in range(1, 11)}
        for nota, total in db.execute(
            select(Avaliacao.nota, func.count(Avaliacao.id))
            .where(Avaliacao.avaliado_id == produtor.id)
            .group_by(Avaliacao.nota)
        ).all():
            distribuicao[str(float(nota))] = total

        avaliacoes = db.execute(
            select(Avaliacao)
            .options(joinedload(Avaliacao.avaliador))
            .where(Avaliacao.avaliado_id == produtor.id)
            .order_by(Avaliacao.data_criacao.desc())
        ).scalars().all()

        produtos = db.execute(
            select(Produto)
            .where(
                Produto.produtor_id == produtor.id,
                Produto.status == "publicado"
            )
            .order_by(Produto.nome)
        ).scalars().all()

        return {
            "produtor": produtor,
            "media": resumo["media"] if resumo else None,
            "total_avaliacoes": resumo["total"] if resumo else 0,
            "distribuicao": distribuicao,
            "avaliacoes": [
                {
                    **avaliacao_para_json(a),
                    "avaliador_nome": nome_para_exibir(a.avaliador) if a.avaliador else "Estabelecimento"
                }
                for a in avaliacoes
            ],
            "produtos": produtos
        }

    finally:
        db.close()
