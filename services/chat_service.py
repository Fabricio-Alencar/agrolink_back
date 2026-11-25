
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

def buscar_negociacao(negociacao_id: int):
    db = SessionLocal()

    try:
        return db.get(Negociacao, negociacao_id)
    finally:
        db.close()


# =========================================================
# VERIFICAR ACESSO À NEGOCIAÇÃO
# =========================================================

def usuario_tem_acesso(negociacao, usuario_id: int):
    if not negociacao:
        return False

    return (
        negociacao.comprador_id == usuario_id
        or negociacao.vendedor_id == usuario_id
    )


# =========================================================
# BUSCAR CONVERSA INICIADA
# =========================================================

def buscar_conversa(db_chat: Session, negociacao_id: int):
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
    conversa = buscar_conversa(db_chat, negociacao_id)

    if conversa:
        return conversa

    conversa = Conversa(
        negociacao_id=negociacao_id,
        iniciada_por_id=usuario_id
    )

    db_chat.add(conversa)

    try:
        db_chat.commit()
        db_chat.refresh(conversa)

        return conversa

    # Outra requisição pode ter criado a conversa simultaneamente.
    except IntegrityError:
        db_chat.rollback()

        conversa = buscar_conversa(
            db_chat,
            negociacao_id
        )

        if conversa:
            return conversa

        raise


# =========================================================
# IDENTIFICAR OUTRO PARTICIPANTE
# =========================================================

def _obter_outro_participante(negociacao, usuario_id: int):
    if negociacao.comprador_id == usuario_id:
        return negociacao.vendedor

    return negociacao.comprador


# =========================================================
# OBTER DATA DE ORDENAÇÃO
# =========================================================

def _obter_data_ordenacao(ultima_mensagem, conversa):
    if ultima_mensagem:
        return ultima_mensagem.data_envio

    return conversa.data_criacao


# =========================================================
# MONTAR DADOS DA CONVERSA
# =========================================================

def _montar_dados_conversa(
    conversa,
    negociacao,
    outro_usuario,
    ultima_mensagem,
    mensagens_nao_lidas
):
    foto_perfil = (
        gerar_url_sas("usuarios", outro_usuario.foto_perfil)
        if outro_usuario.foto_perfil
        else None
    )

    return {
        "conversa_id": conversa.id,
        "negociacao_id": negociacao.id,
        "status_negociacao": negociacao.status,
        "arquivada": (
            str(negociacao.status).lower()
            in ("finalizado", "cancelado")
        ),
        "usuario_id": outro_usuario.id,
        "nome": outro_usuario.nome,
        "tipo": outro_usuario.tipo,
        "foto_perfil": foto_perfil,
        "produto": (
            negociacao.produto.nome
            if negociacao.produto
            else "Produto"
        ),
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
        "tem_mensagens": ultima_mensagem is not None,
        "mensagens_nao_lidas": mensagens_nao_lidas
    }


# =========================================================
# LISTAR CONVERSAS INICIADAS
# =========================================================

def listar_conversas(usuario_id: int, db_chat: Session):
    db = SessionLocal()

    try:
        conversas_iniciadas = (
            db_chat.query(Conversa)
            .order_by(Conversa.data_criacao.desc())
            .all()
        )

        conversas = []

        for conversa in conversas_iniciadas:
            negociacao = db.get(
                Negociacao,
                conversa.negociacao_id
            )

            if not negociacao:
                continue

            if not usuario_tem_acesso(negociacao, usuario_id):
                continue

            outro_usuario = _obter_outro_participante(
                negociacao,
                usuario_id
            )

            if not outro_usuario:
                continue

            ultima_mensagem = buscar_ultima_mensagem(
                db_chat,
                negociacao.id
            )

            mensagens_nao_lidas = contar_mensagens_nao_lidas(
                db_chat,
                negociacao.id,
                usuario_id
            )

            dados_conversa = _montar_dados_conversa(
                conversa,
                negociacao,
                outro_usuario,
                ultima_mensagem,
                mensagens_nao_lidas
            )

            data_ordenacao = _obter_data_ordenacao(
                ultima_mensagem,
                conversa
            )

            conversas.append(
                (data_ordenacao, dados_conversa)
            )

        # Ordena pela atividade mais recente.
        conversas.sort(
            key=lambda item: item[0],
            reverse=True
        )

        return [
            dados_conversa
            for _, dados_conversa in conversas
        ]

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

def buscar_mensagens(db: Session, negociacao_id: int):
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

def buscar_ultima_mensagem(db: Session, negociacao_id: int):
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
