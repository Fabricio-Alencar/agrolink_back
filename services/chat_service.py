from sqlalchemy.orm import Session

from models.mensagem import Mensagem
from models.negociacao import Negociacao

from database import SessionLocal

from services.azure_storage_service import gerar_url_sas


# =========================================================
# BUSCAR NEGOCIAÇÃO
# =========================================================

def buscar_negociacao(
    negociacao_id: int
):

    db = SessionLocal()

    try:

        return db.get(
            Negociacao,
            negociacao_id
        )

    finally:

        db.close()


# =========================================================
# VERIFICAR ACESSO À NEGOCIAÇÃO
# =========================================================

def usuario_tem_acesso(
    negociacao,
    usuario_id: int
):

    if not negociacao:
        return False

    return (
        negociacao.comprador_id == usuario_id
        or
        negociacao.vendedor_id == usuario_id
    )


# =========================================================
# LISTAR CONVERSAS
# =========================================================

def listar_conversas(
    usuario_id: int,
    db_chat: Session
):

    db = SessionLocal()

    try:

        # ==========================================
        # BUSCA AS NEGOCIAÇÕES DO USUÁRIO
        # ==========================================

        negociacoes = (
            db.query(Negociacao)
            .filter(
                (
                    Negociacao.comprador_id == usuario_id
                )
                |
                (
                    Negociacao.vendedor_id == usuario_id
                )
            )
            .all()
        )


        conversas = []


        # ==========================================
        # VERIFICA QUAIS POSSUEM MENSAGENS
        # ==========================================

        for negociacao in negociacoes:

            ultima_mensagem = buscar_ultima_mensagem(
                db_chat,
                negociacao.id
            )

            mensagens_nao_lidas = contar_mensagens_nao_lidas(
                db_chat,
                negociacao.id,
                usuario_id
            )


            # Se não existe mensagem,
            # ainda não existe conversa

            if not ultima_mensagem:

                continue


            # ======================================
            # IDENTIFICA A OUTRA PESSOA
            # ======================================

            if negociacao.comprador_id == usuario_id:

                outro_usuario = negociacao.vendedor

            else:

                outro_usuario = negociacao.comprador


            # ======================================
            # ADICIONA A CONVERSA
            # ======================================

            conversas.append(
                {
                    "negociacao_id": negociacao.id,
                    "usuario_id": outro_usuario.id,
                    "nome": outro_usuario.nome,
                    "tipo": outro_usuario.tipo,
                    "foto_perfil": (
                        gerar_url_sas(
                            "usuarios",
                            outro_usuario.foto_perfil
                        )
                        if outro_usuario.foto_perfil
                        else None
                    ),
                    "produto": (
                        negociacao.produto.nome
                        if negociacao.produto
                        else "Produto"
                    ),
                    "ultima_mensagem": ultima_mensagem.texto,
                    "data_ultima_mensagem":
                        ultima_mensagem.data_envio,
                    "mensagens_nao_lidas":
                        mensagens_nao_lidas
                }
            )


        # ==========================================
        # ORDENA PELA MENSAGEM MAIS RECENTE
        # ==========================================

        conversas.sort(
            key=lambda conversa:
                conversa["data_ultima_mensagem"],
            reverse=True
        )


        return conversas

    finally:

        db.close()


# =========================================================
# CRIAR MENSAGEM
# =========================================================

def criar_mensagem(
    db: Session,
    negociacao_id: int,
    remetente_id: int,
    texto: str
):

    mensagem = Mensagem(
        negociacao_id=negociacao_id,
        remetente_id=remetente_id,
        texto=texto
    )


    db.add(mensagem)

    db.commit()

    db.refresh(mensagem)


    return mensagem


# =========================================================
# BUSCAR MENSAGENS
# =========================================================

def buscar_mensagens(
    db: Session,
    negociacao_id: int
):

    return (
        db.query(Mensagem)
        .filter(
            Mensagem.negociacao_id == negociacao_id
        )
        .order_by(
            Mensagem.data_envio.asc()
        )
        .all()
    )


# =========================================================
# MARCAR MENSAGENS COMO LIDAS
# =========================================================

def marcar_mensagens_como_lidas(
    db: Session,
    negociacao_id: int,
    usuario_id: int
):

    mensagens = (
        db.query(Mensagem)
        .filter(
            Mensagem.negociacao_id == negociacao_id,
            Mensagem.remetente_id != usuario_id,
            Mensagem.lida == False
        )
        .all()
    )


    for mensagem in mensagens:

        mensagem.lida = True


    db.commit()


    return mensagens


# =========================================================
# BUSCAR ÚLTIMA MENSAGEM
# =========================================================

def buscar_ultima_mensagem(
    db: Session,
    negociacao_id: int
):

    return (
        db.query(Mensagem)
        .filter(
            Mensagem.negociacao_id == negociacao_id
        )
        .order_by(
            Mensagem.data_envio.desc()
        )
        .first()
    )


# =========================================================
# CONTAR MENSAGENS NÃO LIDAS
# =========================================================

def contar_mensagens_nao_lidas(
    db: Session,
    negociacao_id: int,
    usuario_id: int
):

    return (
        db.query(Mensagem)
        .filter(
            Mensagem.negociacao_id == negociacao_id,
            Mensagem.remetente_id != usuario_id,
            Mensagem.lida == False
        )
        .count()
    )