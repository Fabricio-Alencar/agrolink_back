
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from models.mensagem import Mensagem
from models.conversa import Conversa
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
# BUSCAR CONVERSA INICIADA
# =========================================================

def buscar_conversa(
    db_chat: Session,
    negociacao_id: int
):

    return (
        db_chat.query(Conversa)
        .filter(
            Conversa.negociacao_id == negociacao_id
        )
        .first()
    )


# =========================================================
# INICIAR CONVERSA
# =========================================================

def iniciar_conversa(
    db_chat: Session,
    negociacao_id: int,
    usuario_id: int
):

    # ==========================================
    # VERIFICA SE A CONVERSA JÁ EXISTE
    # ==========================================

    conversa = buscar_conversa(
        db_chat,
        negociacao_id
    )

    if conversa:
        return conversa


    # ==========================================
    # CRIA O REGISTRO DA CONVERSA
    # ==========================================

    conversa = Conversa(
        negociacao_id=negociacao_id,
        iniciada_por_id=usuario_id
    )

    db_chat.add(conversa)

    try:

        db_chat.commit()

        db_chat.refresh(conversa)

        return conversa

    except IntegrityError:

        # ======================================
        # OUTRA REQUISIÇÃO PODE TER CRIADO
        # A CONVERSA AO MESMO TEMPO
        # ======================================

        db_chat.rollback()

        conversa = buscar_conversa(
            db_chat,
            negociacao_id
        )

        if conversa:
            return conversa

        raise


# =========================================================
# LISTAR CONVERSAS INICIADAS
# =========================================================

def listar_conversas(
    usuario_id: int,
    db_chat: Session
):

    db = SessionLocal()

    try:

        # ==========================================
        # BUSCA SOMENTE CONVERSAS INICIADAS
        # ==========================================

        conversas_iniciadas = (
            db_chat.query(Conversa)
            .order_by(
                Conversa.data_criacao.desc()
            )
            .all()
        )

        conversas = []


        # ==========================================
        # PROCESSA CADA CONVERSA
        # ==========================================

        for conversa in conversas_iniciadas:

            negociacao = db.get(
                Negociacao,
                conversa.negociacao_id
            )

            if not negociacao:
                continue


            # ======================================
            # CONFERE SE O USUÁRIO PARTICIPA
            # DA NEGOCIAÇÃO
            # ======================================

            if not usuario_tem_acesso(
                negociacao,
                usuario_id
            ):
                continue


            # ======================================
            # BUSCA A ÚLTIMA MENSAGEM
            # ======================================

            ultima_mensagem = buscar_ultima_mensagem(
                db_chat,
                negociacao.id
            )


            # ======================================
            # CONTA MENSAGENS NÃO LIDAS
            # ======================================

            mensagens_nao_lidas = contar_mensagens_nao_lidas(
                db_chat,
                negociacao.id,
                usuario_id
            )


            # ======================================
            # IDENTIFICA O OUTRO PARTICIPANTE
            # ======================================

            if negociacao.comprador_id == usuario_id:

                outro_usuario = negociacao.vendedor

            else:

                outro_usuario = negociacao.comprador


            if not outro_usuario:
                continue


            # ======================================
            # DADOS DA CONVERSA
            # ======================================

            foto_perfil = (
                gerar_url_sas(
                    "usuarios",
                    outro_usuario.foto_perfil
                )
                if outro_usuario.foto_perfil
                else None
            )

            data_ordenacao = (
                ultima_mensagem.data_envio
                if ultima_mensagem
                else conversa.data_criacao
            )


            conversas.append(
                {
                    "conversa_id": conversa.id,
                    "negociacao_id": negociacao.id,
                    "usuario_id": outro_usuario.id,
                    "nome": outro_usuario.nome,
                    "tipo": outro_usuario.tipo,
                    "foto_perfil": foto_perfil,

                    "produto": (
                        negociacao.produto.nome
                        if negociacao.produto
                        else "Produto"
                    ),

                    # None significa que ainda não há mensagens.
                    # Não criamos mensagens fictícias.
                    "ultima_mensagem": (
                        ultima_mensagem.texto
                        if ultima_mensagem
                        else None
                    ),

                    "data_ultima_mensagem": (
                        ultima_mensagem.data_envio
                        if ultima_mensagem
                        else None
                    ),

                    "data_criacao": conversa.data_criacao,

                    "tem_mensagens": (
                        ultima_mensagem is not None
                    ),

                    "mensagens_nao_lidas": mensagens_nao_lidas,

                    # Campo interno utilizado na ordenação.
                    "_data_ordenacao": data_ordenacao
                }
            )


        # ==========================================
        # ORDENA PELA ATIVIDADE MAIS RECENTE
        # ==========================================

        conversas.sort(
            key=lambda item: item["_data_ordenacao"],
            reverse=True
        )


        # ==========================================
        # REMOVE CAMPO INTERNO
        # ==========================================

        for conversa in conversas:
            conversa.pop("_data_ordenacao")


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
