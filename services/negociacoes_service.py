from models import Usuario, Negociacao
from database import SessionLocal
from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.orm import joinedload


# Ordena pela última mudança (status, confirmação ou avaliação);
# pedidos antigos, sem essa data, usam a data de criação
ORDEM_MAIS_RECENTE_PRIMEIRO = func.coalesce(
    Negociacao.data_atualizacao,
    Negociacao.data_criacao
).desc()

# =========================
# BUSCA TODAS AS NEGOCIAÇÕES DE UM USUARIO
# =========================
def listar_negociacoes(user_id, tipo_de_negociante):
    db = SessionLocal()

    try:
        tipo = tipo_de_negociante.lower()

        # 1. Buscamos o objeto do usuário no banco
        usuario = db.get(Usuario, user_id)

        if not usuario:
            print(f"[ERRO] Usuário ID {user_id} não encontrado.")
            return []

        # 2. Usamos os relacionamentos definidos no ARQUIVO 3
        if tipo == "produtor":
            # Retorna as negociações onde este usuário é o vendedor_id
            print(f"[DEBUG] Listando negociações como Vendedor para o usuário {user_id}")

            # Busca as negociações e carrega antecipadamente:
            # - comprador
            # - vendedor
            # - produto
            negociacoes = db.execute(
                select(Negociacao)
                .options(
                    joinedload(Negociacao.comprador),
                    joinedload(Negociacao.vendedor),
                    joinedload(Negociacao.produto)
                )
                .where(
                    Negociacao.vendedor_id == user_id,
                    Negociacao.oculto_vendedor == False
                )
                # Pedido com mudança mais recente primeiro
                .order_by(ORDEM_MAIS_RECENTE_PRIMEIRO, Negociacao.id.desc())
            ).scalars().all()

            return negociacoes

        elif tipo == "estabelecimento":
            # Retorna as negociações onde este usuário é o comprador_id
            print(f"[DEBUG] Listando negociações como Comprador para o usuário {user_id}")

            # Busca as negociações e carrega antecipadamente:
            # - comprador
            # - vendedor
            # - produto
            negociacoes = db.execute(
                select(Negociacao)
                .options(
                    joinedload(Negociacao.comprador),
                    joinedload(Negociacao.vendedor),
                    joinedload(Negociacao.produto)
                )
                .where(
                    Negociacao.comprador_id == user_id,
                    Negociacao.oculto_comprador == False
                )
                # Pedido com mudança mais recente primeiro
                .order_by(ORDEM_MAIS_RECENTE_PRIMEIRO, Negociacao.id.desc())
            ).scalars().all()

            return negociacoes

        else:
            print(f"[AVISO] Tipo de negociante '{tipo}' inválido.")
            return []

    finally:
        db.close()


# =========================
# ATUALIZAR STATUS DA NEGOCIAÇÃO
# =========================
def atualizar_status_negociacao(negociacao_id, novo_status, user_id):
    db = SessionLocal()

    try:
        negociacao = db.get(Negociacao, negociacao_id)

        if not negociacao:
            return {"erro": "Negociação não encontrada"}, 404

        if user_id not in (negociacao.comprador_id, negociacao.vendedor_id):
            return {"erro": "Você não possui acesso a esta negociação."}, 403

        # Quem pode levar o pedido para cada status, e a partir de qual status:
        # - Aceito / Recusado: só o produtor, enquanto o pedido está pendente
        # - Cancelado: o estabelecimento enquanto pendente; qualquer lado depois de aceito
        # (Entregue e Finalizado só acontecem pelas confirmações de entrega/recebimento)
        sou_produtor = user_id == negociacao.vendedor_id
        atual = (negociacao.status or "pendente").lower()
        novo = str(novo_status).strip().lower()

        permitido = (
            (novo in ("aceito", "recusado") and sou_produtor and atual == "pendente")
            or (novo == "cancelado" and atual == "pendente" and not sou_produtor)
            or (novo == "cancelado" and atual == "aceito")
        )

        if not permitido:
            return {"erro": f"Não é possível mudar o pedido de {negociacao.status} para {novo_status}."}, 400

        negociacao.status = novo.capitalize()
        negociacao.data_atualizacao = datetime.utcnow()
        db.commit()

        return {"mensagem": f"Status atualizado para {negociacao.status}"}, 200

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


# =========================
# REGISTRAR CONFIRMAÇÃO (ENTREGA/RECEBIMENTO)
# =========================
def registrar_confirmacao_service(negociacao_id, acao, user_id):
    db = SessionLocal()

    try:
        negociacao = db.get(Negociacao, negociacao_id)

        if not negociacao:
            return {"erro": "Negociação não encontrada"}, 404

        # Só dá para confirmar pedido aceito (ou já entregue, no caso do recebimento)
        if (negociacao.status or "").lower() not in ("aceito", "entregue"):
            return {"erro": f"Não é possível confirmar um pedido {negociacao.status}."}, 400

        # Entrega é confirmada pelo produtor; recebimento, pelo estabelecimento
        if acao == 'confirmar_entrega' and user_id != negociacao.vendedor_id:
            return {"erro": "Apenas o produtor pode confirmar a entrega"}, 403

        if acao == 'confirmar_recebimento' and user_id != negociacao.comprador_id:
            return {"erro": "Apenas o estabelecimento pode confirmar o recebimento"}, 403

        # Marca qual lado confirmou
        if acao == 'confirmar_entrega':
            negociacao.entrega_confirmada = True
            # Adiciona a mudança para Entregue
            negociacao.status = 'Entregue'

        elif acao == 'confirmar_recebimento':
            negociacao.recebimento_confirmado = True
            # Se o estabelecimento recebeu, a entrega aconteceu: o pedido já
            # finaliza e a tela de avaliação pode abrir na hora
            negociacao.entrega_confirmada = True
        else:
            return {"erro": "Ação inválida"}, 400

        # Lógica de finalização automática
        if negociacao.entrega_confirmada and negociacao.recebimento_confirmado:
            negociacao.status = 'Finalizado'

        negociacao.data_atualizacao = datetime.utcnow()
        db.commit()

        return {
            "mensagem": "Confirmação registrada com sucesso",
            "status_atual": negociacao.status
        }, 200

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


# =========================
# DELETAR/OCULTAR NEGOCIAÇÃO DO HISTÓRICO
# =========================
def deletar_negociacao_service(negociacao_id, user_id):
    db = SessionLocal()

    try:
        negociacao = db.get(Negociacao, negociacao_id)

        if not negociacao:
            return {"erro": "Negociação não encontrada"}, 404

        # 1. Marca como oculto para a pessoa que clicou na lixeira
        if negociacao.comprador_id == user_id:
            negociacao.oculto_comprador = True
        elif negociacao.vendedor_id == user_id:
            negociacao.oculto_vendedor = True
        else:
            return {"erro": "Acesso negado"}, 403

        #Verifica se ambos já ocultaram. Se sim, apaga do banco de vez!
        if negociacao.oculto_comprador and negociacao.oculto_vendedor:
            db.delete(negociacao)
            mensagem = "Negociação excluída permanentemente do banco de dados."
        else:
            mensagem = "Negociação ocultada da sua tela."

        db.commit()

        return {"mensagem": mensagem}, 200

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()

# =========================
# BUSCAR UMA NEGOCIAÇÃO ESPECÍFICA
# =========================
def buscar_negociacao(negociacao_id):
    db = SessionLocal()

    try:

        negociacao = db.execute(
            select(Negociacao)
            .options(
                joinedload(Negociacao.comprador),
                joinedload(Negociacao.vendedor),
                joinedload(Negociacao.produto)
            )
            .where(
                Negociacao.id == negociacao_id
            )
        ).scalar_one_or_none()

        return negociacao

    finally:
        db.close()

