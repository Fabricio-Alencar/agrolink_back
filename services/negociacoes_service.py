from models import Usuario, Negociacao
from database import SessionLocal
from sqlalchemy import select
from sqlalchemy.orm import joinedload

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
def atualizar_status_negociacao(negociacao_id, novo_status):
    db = SessionLocal()

    try:
        negociacao = db.get(Negociacao, negociacao_id)

        if not negociacao:
            return {"erro": "Negociação não encontrada"}, 404

        negociacao.status = novo_status
        db.commit()

        return {"mensagem": f"Status atualizado para {novo_status}"}, 200

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


# =========================
# REGISTRAR CONFIRMAÇÃO (ENTREGA/RECEBIMENTO)
# =========================
def registrar_confirmacao_service(negociacao_id, acao):
    db = SessionLocal()

    try:
        negociacao = db.get(Negociacao, negociacao_id)

        if not negociacao:
            return {"erro": "Negociação não encontrada"}, 404

        # Marca qual lado confirmou
        if acao == 'confirmar_entrega':
            negociacao.entrega_confirmada = True
            # Adiciona a mudança para Entregue
            negociacao.status = 'Entregue'

        elif acao == 'confirmar_recebimento':
            negociacao.recebimento_confirmado = True
        else:
            return {"erro": "Ação inválida"}, 400

        # Lógica de finalização automática
        if negociacao.entrega_confirmada and negociacao.recebimento_confirmado:
            negociacao.status = 'Finalizado'

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
