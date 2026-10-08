from fastapi import (
    APIRouter,
    Depends,
    WebSocket,
    WebSocketDisconnect,
    HTTPException
)

from auth.security import decodificar_token
from auth.dependencies import get_current_user

from database import SessionLocal
from models.usuario import Usuario

from sqlalchemy.orm import Session

from schemas.chat_schema import MensagemCriar

from chat_database import get_chat_db, SessionChat

from services.chat_service import (
    buscar_negociacao,
    usuario_tem_acesso,
    listar_conversas,
    criar_mensagem,
    buscar_mensagens,
    marcar_mensagens_como_lidas,
    contar_mensagens_nao_lidas
)


router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)


# =========================================================
# CONEXÕES DO CHAT POR NEGOCIAÇÃO
# =========================================================

conexoes_chat = {}


# =========================================================
# CONEXÕES GERAIS POR USUÁRIO
# =========================================================

conexoes_usuarios = {}


# =========================================================
# AUTENTICAR WEBSOCKET
# =========================================================

def autenticar_websocket(websocket):

    access_token = websocket.cookies.get("access_token")

    if not access_token:
        return None

    try:

        payload = decodificar_token(access_token)

        user_id = payload.get("sub")
        tipo = payload.get("tipo")

        if not user_id or not tipo:
            return None

        db = SessionLocal()

        try:

            usuario = db.get(
                Usuario,
                int(user_id)
            )

            if not usuario:
                return None

            return {
                "user_id": usuario.id,
                "tipo": usuario.tipo,
                "nome": usuario.nome
            }

        finally:

            db.close()

    except Exception:

        return None


# =========================================================
# TESTE
# =========================================================

@router.get("/")
def teste_chat():

    return {
        "message": "Chat funcionando!"
    }


# =========================================================
# LISTAR CONVERSAS
# =========================================================

@router.get("/conversas")
def listar_conversas_route(
    usuario=Depends(get_current_user),
    db_chat: Session = Depends(get_chat_db)
):

    usuario_id = usuario["user_id"]


    print(
        "👤 USUÁRIO LOGADO NO CHAT:",
        usuario_id
    )


    conversas = listar_conversas(
        usuario_id,
        db_chat
    )


    print(
        "💬 CONVERSAS FINAIS:",
        conversas
    )


    return conversas


# =========================================================
# VERIFICAR ACESSO À NEGOCIAÇÃO
# =========================================================

@router.get("/acesso/{negociacao_id}")
def verificar_acesso_negociacao(
    negociacao_id: int,
    usuario=Depends(get_current_user)
):

    usuario_id = usuario["user_id"]


    # ==========================================
    # BUSCA A NEGOCIAÇÃO
    # ==========================================

    negociacao = buscar_negociacao(
        negociacao_id
    )


    # ==========================================
    # NEGOCIAÇÃO NÃO EXISTE
    # ==========================================

    if not negociacao:

        return {
            "permitido": False
        }


    # ==========================================
    # VERIFICA SE O USUÁRIO PARTICIPA
    # ==========================================

    permitido = usuario_tem_acesso(
        negociacao,
        usuario_id
    )


    return {
        "permitido": permitido
    }


# =========================================================
# ENVIAR MENSAGEM
# =========================================================

@router.post("/mensagens")
def enviar_mensagem(
    dados: MensagemCriar,
    usuario=Depends(get_current_user),
    db: Session = Depends(get_chat_db)
):

    usuario_id = usuario["user_id"]


    # ==========================================
    # BUSCA A NEGOCIAÇÃO
    # ==========================================

    negociacao = buscar_negociacao(
        dados.negociacao_id
    )


    # ==========================================
    # NEGOCIAÇÃO NÃO EXISTE
    # ==========================================

    if not negociacao:

        raise HTTPException(
            status_code=404,
            detail="Negociação não encontrada."
        )


    # ==========================================
    # VERIFICA ACESSO DO USUÁRIO
    # ==========================================

    if not usuario_tem_acesso(
        negociacao,
        usuario_id
    ):

        raise HTTPException(
            status_code=403,
            detail="Você não possui acesso a esta negociação."
        )


    # ==========================================
    # CRIA A MENSAGEM
    # ==========================================

    mensagem = criar_mensagem(
        db,
        dados.negociacao_id,
        usuario_id,
        dados.texto
    )


    return {
        "id": mensagem.id,
        "negociacao_id": mensagem.negociacao_id,
        "remetente_id": mensagem.remetente_id,
        "texto": mensagem.texto,
        "data_envio": mensagem.data_envio,
        "lida": mensagem.lida
    }


# =========================================================
# LISTAR MENSAGENS
# =========================================================

@router.get("/mensagens/{negociacao_id}")
async def listar_mensagens(
    negociacao_id: int,
    usuario=Depends(get_current_user),
    db: Session = Depends(get_chat_db)
):

    usuario_id = usuario["user_id"]


    # ==========================================
    # BUSCA A NEGOCIAÇÃO
    # ==========================================

    negociacao = buscar_negociacao(
        negociacao_id
    )


    # ==========================================
    # NEGOCIAÇÃO NÃO EXISTE
    # ==========================================

    if not negociacao:

        raise HTTPException(
            status_code=404,
            detail="Negociação não encontrada."
        )


    # ==========================================
    # VERIFICA ACESSO DO USUÁRIO
    # ==========================================

    if not usuario_tem_acesso(
        negociacao,
        usuario_id
    ):

        raise HTTPException(
            status_code=403,
            detail="Você não possui acesso a esta negociação."
        )


    # ==========================================
    # MARCA AS MENSAGENS COMO LIDAS
    # ==========================================

    mensagens_lidas = marcar_mensagens_como_lidas(
        db,
        negociacao_id,
        usuario_id
    )


    # ==========================================
    # IDENTIFICA O OUTRO PARTICIPANTE
    # ==========================================

    if negociacao.comprador_id == usuario_id:

        outro_usuario_id = (
            negociacao.vendedor_id
        )

    else:

        outro_usuario_id = (
            negociacao.comprador_id
        )


    # ==========================================
    # ENVIA NOTIFICAÇÃO DE LEITURA
    # ==========================================

    if mensagens_lidas:

        print(
            "👁️ MENSAGENS MARCADAS COMO LIDAS:",
            negociacao_id
        )


        print(
            "👤 USUÁRIO QUE LEU:",
            usuario_id
        )


        print(
            "📨 NOTIFICANDO USUÁRIO:",
            outro_usuario_id
        )


        notificacao = {
            "tipo": "mensagens_lidas",
            "negociacao_id": negociacao_id,
            "leitor_id": usuario_id,
            "mensagem_ids": [
                mensagem.id
                for mensagem in mensagens_lidas
            ]
        }


        # ==========================================
        # VERIFICA SE O OUTRO USUÁRIO ESTÁ CONECTADO
        # ==========================================

        if outro_usuario_id in conexoes_usuarios:

            for conexao_usuario in conexoes_usuarios[
                outro_usuario_id
            ]:

                try:

                    await conexao_usuario.send_json(
                        notificacao
                    )


                except Exception as erro:

                    print(
                        "❌ ERRO AO ENVIAR NOTIFICAÇÃO DE LEITURA:",
                        erro
                    )


    # ==========================================
    # BUSCA AS MENSAGENS
    # ==========================================

    mensagens = buscar_mensagens(
        db,
        negociacao_id
    )


    return [
        {
            "id": mensagem.id,
            "negociacao_id": mensagem.negociacao_id,
            "remetente_id": mensagem.remetente_id,
            "texto": mensagem.texto,
            "data_envio": mensagem.data_envio,
            "lida": mensagem.lida
        }
        for mensagem in mensagens
    ]


# =========================================================
# WEBSOCKET GERAL DO USUÁRIO
# =========================================================

@router.websocket("/ws")
async def websocket_usuario(
    websocket: WebSocket
):

    print(
        "🟢 WEBSOCKET GERAL CHEGOU NO BACKEND!"
    )


    # ==========================================
    # AUTENTICA USUÁRIO
    # ==========================================

    usuario = autenticar_websocket(
        websocket
    )


    if not usuario:

        print(
            "🔴 WEBSOCKET GERAL NÃO AUTENTICADO!"
        )

        await websocket.close(
            code=1008
        )

        return


    usuario_id = usuario["user_id"]


    print(
        "👤 USUÁRIO CONECTADO AO WEBSOCKET GERAL:",
        usuario_id
    )


    # ==========================================
    # ACEITA A CONEXÃO
    # ==========================================

    await websocket.accept()


    # ==========================================
    # CRIA LISTA DO USUÁRIO
    # ==========================================

    if usuario_id not in conexoes_usuarios:

        conexoes_usuarios[usuario_id] = []


    # ==========================================
    # ADICIONA CONEXÃO
    # ==========================================

    conexoes_usuarios[usuario_id].append(
        websocket
    )


    try:

        await websocket.send_json(
            {
                "tipo": "conexao",
                "mensagem": "WebSocket geral conectado."
            }
        )


        # ==========================================
        # MANTÉM CONEXÃO ABERTA
        # ==========================================

        while True:

            await websocket.receive_text()


    except WebSocketDisconnect:

        print(
            "🔌 WEBSOCKET GERAL DESCONECTADO:",
            usuario_id
        )


    finally:

        # ==========================================
        # REMOVE CONEXÃO
        # ==========================================

        if usuario_id in conexoes_usuarios:

            conexoes_usuarios[usuario_id] = [
                conexao
                for conexao in conexoes_usuarios[usuario_id]
                if conexao != websocket
            ]


            # ======================================
            # REMOVE USUÁRIO SE NÃO POSSUI CONEXÕES
            # ======================================

            if not conexoes_usuarios[usuario_id]:

                del conexoes_usuarios[usuario_id]


# =========================================================
# WEBSOCKET DO CHAT
# =========================================================

@router.websocket("/ws/{negociacao_id}")
async def chat_websocket(
    websocket: WebSocket,
    negociacao_id: int
):

    print(
        "🟢 WEBSOCKET CHEGOU NO BACKEND!",
        "negociação =",
        negociacao_id
    )


    usuario = autenticar_websocket(
        websocket
    )


    if not usuario:

        await websocket.close(
            code=1008
        )

        return


    remetente_id = usuario["user_id"]


    # ==========================================
    # BUSCA A NEGOCIAÇÃO
    # ==========================================

    negociacao = buscar_negociacao(
        negociacao_id
    )


    if not negociacao:

        await websocket.close(
            code=1008
        )

        return


    # ==========================================
    # VERIFICA ACESSO DO USUÁRIO
    # ==========================================

    if not usuario_tem_acesso(
        negociacao,
        remetente_id
    ):

        await websocket.close(
            code=1008
        )

        return


    await websocket.accept()


    if negociacao_id not in conexoes_chat:

        conexoes_chat[negociacao_id] = []


    conexoes_chat[negociacao_id].append(
        (
            remetente_id,
            websocket
        )
    )


    db = SessionChat()


    try:

        try:

            while True:

                texto = await websocket.receive_text()


                print(
                    "📩 MENSAGEM RECEBIDA PELO BACKEND:"
                )


                print(
                    texto
                )


                mensagem = criar_mensagem(
                    db,
                    negociacao_id,
                    remetente_id,
                    texto
                )


                print(
                    "💾 MENSAGEM SALVA NO BANCO:"
                )


                print(
                    mensagem.id
                )


                # ==========================================
                # ENVIA A MENSAGEM PARA AS CONEXÕES DO CHAT
                # ==========================================

                for usuario_id, conexao in conexoes_chat[negociacao_id]:

                    print(
                        "📤 ENVIANDO MENSAGEM PARA:",
                        usuario_id
                    )


                    mensagem_json = {
                        "id": mensagem.id,
                        "negociacao_id": mensagem.negociacao_id,
                        "remetente_id": mensagem.remetente_id,
                        "texto": mensagem.texto,
                        "data_envio": mensagem.data_envio.isoformat(),
                        "lida": mensagem.lida
                    }


                    # ==========================================
                    # ENVIA PARA O PRÓPRIO REMETENTE
                    # ==========================================

                    if usuario_id == remetente_id:

                        await conexao.send_json(
                            {
                                "tipo": "confirmacao_mensagem",
                                **mensagem_json
                            }
                        )


                    # ==========================================
                    # ENVIA PARA O OUTRO USUÁRIO
                    # ==========================================

                    else:

                        await conexao.send_json(
                            mensagem_json
                        )


                # ==========================================
                # IDENTIFICA O OUTRO PARTICIPANTE
                # ==========================================

                if negociacao.comprador_id == remetente_id:

                    outro_usuario_id = (
                        negociacao.vendedor_id
                    )

                else:

                    outro_usuario_id = (
                        negociacao.comprador_id
                    )


                # ==========================================
                # ENVIA NOTIFICAÇÃO PELO WEBSOCKET GERAL
                # ==========================================

                if outro_usuario_id in conexoes_usuarios:

                    print(
                        "🔔 ENVIANDO NOTIFICAÇÃO PARA USUÁRIO:",
                        outro_usuario_id
                    )


                    notificacao = {
                        "tipo": "nova_mensagem",
                        "negociacao_id": negociacao_id,
                        "remetente_id": remetente_id,
                        "texto": mensagem.texto,
                        "data_envio": mensagem.data_envio.isoformat(),
                        "lida": False
                    }


                    for conexao_usuario in conexoes_usuarios[
                        outro_usuario_id
                    ]:

                        try:

                            await conexao_usuario.send_json(
                                notificacao
                            )

                        except Exception as erro:

                            print(
                                "❌ Erro ao enviar notificação:",
                                erro
                            )


        except WebSocketDisconnect:

            pass


    finally:

        db.close()


        conexoes_chat[negociacao_id] = [
            conexao
            for conexao in conexoes_chat[negociacao_id]
            if conexao[0] != remetente_id
        ]
