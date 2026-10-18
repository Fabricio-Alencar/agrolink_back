from fastapi import (
    APIRouter,
    Depends,
    WebSocket,
    WebSocketDisconnect,
    HTTPException,
    Query
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
    iniciar_conversa,
    buscar_conversa,
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

def autenticar_websocket(websocket: WebSocket, token: str = None):
    access_token = token or websocket.cookies.get("access_token")

    if not access_token:
        print("❌ [Auth WS] Nenhum token encontrado na query nem nos cookies.")
        return None

    try:
        payload = decodificar_token(access_token)

        user_id = payload.get("sub")
        tipo = payload.get("tipo")

        if not user_id or not tipo:
            print("❌ [Auth WS] Payload do token inválido (sub ou tipo ausentes).")
            return None

        db = SessionLocal()

        try:
            usuario = db.get(
                Usuario,
                int(user_id)
            )

            if not usuario:
                print(f"❌ [Auth WS] Usuário ID {user_id} não encontrado no banco de dados.")
                return None

            print(f"✅ [Auth WS] Usuário autenticado com sucesso: ID {usuario.id} ({usuario.nome})")

            return {
                "user_id": usuario.id,
                "tipo": usuario.tipo,
                "nome": usuario.nome
            }

        finally:
            db.close()

    except Exception as e:
        print(f"❌ [Auth WS] Erro ao decodificar token ou buscar usuário: {e}")
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

    return listar_conversas(
        usuario_id,
        db_chat
    )


# =========================================================
# INICIAR CONVERSA PELO BOTÃO CONVERSAR
# =========================================================

@router.post("/conversas/{negociacao_id}/iniciar")
def iniciar_conversa_route(
    negociacao_id: int,
    usuario=Depends(get_current_user),
    db_chat: Session = Depends(get_chat_db)
):

    usuario_id = usuario["user_id"]

    # ==========================================
    # BUSCA A NEGOCIAÇÃO
    # ==========================================

    negociacao = buscar_negociacao(
        negociacao_id
    )

    if not negociacao:

        raise HTTPException(
            status_code=404,
            detail="Negociação não encontrada."
        )

    # ==========================================
    # VALIDA O ACESSO
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
    # CRIA OU REUTILIZA A CONVERSA
    # ==========================================

    conversa = iniciar_conversa(
        db_chat,
        negociacao_id,
        usuario_id
    )

    return {
        "conversa_id": conversa.id,
        "negociacao_id": conversa.negociacao_id,
        "iniciada_por_id": conversa.iniciada_por_id,
        "data_criacao": conversa.data_criacao
    }


# =========================================================
# VERIFICAR ACESSO À NEGOCIAÇÃO
# =========================================================

@router.get("/acesso/{negociacao_id}")
def verificar_acesso_negociacao(
    negociacao_id: int,
    usuario=Depends(get_current_user)
):

    usuario_id = usuario["user_id"]

    negociacao = buscar_negociacao(
        negociacao_id
    )

    if not negociacao:

        return {
            "permitido": False
        }

    permitido = usuario_tem_acesso(
        negociacao,
        usuario_id
    )

    return {
        "permitido": permitido
    }


# =========================================================
# ENVIAR MENSAGEM VIA REST
# =========================================================

@router.post("/mensagens")
def enviar_mensagem(
    dados: MensagemCriar,
    usuario=Depends(get_current_user),
    db: Session = Depends(get_chat_db)
):

    usuario_id = usuario["user_id"]

    negociacao = buscar_negociacao(
        dados.negociacao_id
    )

    if not negociacao:

        raise HTTPException(
            status_code=404,
            detail="Negociação não encontrada."
        )

    if not usuario_tem_acesso(
        negociacao,
        usuario_id
    ):

        raise HTTPException(
            status_code=403,
            detail="Você não possui acesso a esta negociação."
        )

    # ==========================================
    # EXIGE QUE A CONVERSA TENHA SIDO INICIADA
    # ==========================================

    conversa = buscar_conversa(
        db,
        dados.negociacao_id
    )

    if not conversa:

        raise HTTPException(
            status_code=409,
            detail="Inicie a conversa pelo botão Conversar antes de enviar mensagens."
        )

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

    negociacao = buscar_negociacao(
        negociacao_id
    )

    if not negociacao:

        raise HTTPException(
            status_code=404,
            detail="Negociação não encontrada."
        )

    if not usuario_tem_acesso(
        negociacao,
        usuario_id
    ):

        raise HTTPException(
            status_code=403,
            detail="Você não possui acesso a esta negociação."
        )

    # ==========================================
    # VERIFICA SE A CONVERSA FOI INICIADA
    # ==========================================

    conversa = buscar_conversa(
        db,
        negociacao_id
    )

    if not conversa:

        raise HTTPException(
            status_code=404,
            detail="Esta conversa ainda não foi iniciada."
        )

    # ==========================================
    # MARCA MENSAGENS COMO LIDAS
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

        outro_usuario_id = negociacao.vendedor_id

    else:

        outro_usuario_id = negociacao.comprador_id

    # ==========================================
    # NOTIFICA SOBRE A LEITURA
    # ==========================================

    if mensagens_lidas:

        notificacao = {
            "tipo": "mensagens_lidas",
            "negociacao_id": negociacao_id,
            "leitor_id": usuario_id,
            "mensagem_ids": [
                mensagem.id
                for mensagem in mensagens_lidas
            ]
        }

        if outro_usuario_id in conexoes_usuarios:

            for conexao_usuario in list(
                conexoes_usuarios[outro_usuario_id]
            ):

                try:

                    await conexao_usuario.send_json(
                        notificacao
                    )

                except Exception as erro:

                    print(
                        f"❌ [REST Listar Mensagens] Erro ao notificar leitura para usuário {outro_usuario_id}:",
                        erro
                    )

    # ==========================================
    # RETORNA AS MENSAGENS
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
    websocket: WebSocket,
    token: str = Query(None)
):
    print("🔵 [WS Geral] Tentativa de conexão recebida...")

    usuario = autenticar_websocket(
        websocket,
        token
    )

    if not usuario:
        print("❌ [WS Geral] Falha de autenticação. Fechando conexão com código 1008.")
        await websocket.close(
            code=1008
        )
        return

    usuario_id = usuario["user_id"]

    await websocket.accept()
    print(f"✅ [WS Geral] Conexão aceita para o usuário ID: {usuario_id} ({usuario['nome'])})")

    if usuario_id not in conexoes_usuarios:
        conexoes_usuarios[usuario_id] = []

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

        while True:

            await websocket.receive_text()

    except WebSocketDisconnect:

        print(
            f"🔌 [WS Geral] WebSocket geral desconectado para o usuário ID: {usuario_id}"
        )

    finally:

        if usuario_id in conexoes_usuarios:

            conexoes_usuarios[usuario_id] = [
                conexao
                for conexao in conexoes_usuarios[usuario_id]
                if conexao is not websocket
            ]

            if not conexoes_usuarios[usuario_id]:
                del conexoes_usuarios[usuario_id]
                print(f"🗑️ [WS Geral] Todas as conexões do usuário {usuario_id} foram limpas.")


# =========================================================
# WEBSOCKET DO CHAT
# =========================================================

@router.websocket("/ws/{negociacao_id}")
async def chat_websocket(
    websocket: WebSocket,
    negociacao_id: int,
    token: str = Query(None)
):
    print(f"🔵 [WS Chat] Tentativa de conexão na negociação ID: {negociacao_id}...")

    usuario = autenticar_websocket(
        websocket,
        token
    )

    if not usuario:
        print("❌ [WS Chat] Falha de autenticação. Fechando conexão com código 1008.")
        await websocket.close(
            code=1008
        )
        return

    remetente_id = usuario["user_id"]

    negociacao = buscar_negociacao(
        negociacao_id
    )

    if not negociacao:
        print(f"❌ [WS Chat] Negociação {negociacao_id} não encontrada. Fechando conexão.")
        await websocket.close(
            code=1008
        )
        return

    if not usuario_tem_acesso(
        negociacao,
        remetente_id
    ):
        print(f"❌ [WS Chat] Usuário {remetente_id} não tem acesso à negociação {negociacao_id}. Fechando conexão.")
        await websocket.close(
            code=1008
        )
        return

    # ==========================================
    # SÓ PERMITE CONECTAR A UMA CONVERSA INICIADA
    # ==========================================

    db = SessionChat()

    conversa = buscar_conversa(
        db,
        negociacao_id
    )

    if not conversa:
        print(f"❌ [WS Chat] Conversa da negociação {negociacao_id} ainda não foi iniciada. Fechando conexão.")
        db.close()

        await websocket.close(
            code=1008
        )

        return

    # ==========================================
    # ACEITA E REGISTRA A CONEXÃO
    # ==========================================

    await websocket.accept()
    print(f"✅ [WS Chat] Conexão aceita! Usuário {remetente_id} conectado na negociação {negociacao_id}")

    if negociacao_id not in conexoes_chat:
        conexoes_chat[negociacao_id] = []

    conexoes_chat[negociacao_id].append(
        (
            remetente_id,
            websocket
        )
    )

    try:

        while True:

            texto = await websocket.receive_text()
            print(f"📩 [WS Chat] Mensagem recebida na negociação {negociacao_id} do usuário {remetente_id}: '{texto}'")

            # ======================================
            # SALVA A MENSAGEM
            # ======================================

            mensagem = criar_mensagem(
                db,
                negociacao_id,
                remetente_id,
                texto
            )

            # ======================================
            # IDENTIFICA O OUTRO PARTICIPANTE
            # ======================================

            if negociacao.comprador_id == remetente_id:

                outro_usuario_id = negociacao.vendedor_id

            else:

                outro_usuario_id = negociacao.comprador_id

            # ======================================
            # VERIFICA SE O DESTINATÁRIO ESTÁ
            # COM A CONVERSA ABERTA
            # ======================================

            destinatario_no_chat = any(
                usuario_id == outro_usuario_id
                for usuario_id, conexao in
                conexoes_chat.get(negociacao_id, [])
            )

            # ======================================
            # MARCA COMO LIDA SE O DESTINATÁRIO
            # ESTIVER CONECTADO À CONVERSA
            # ======================================

            if destinatario_no_chat:
                print(f"👀 [WS Chat] Destinatário {outro_usuario_id} está na sala. Marcando mensagem {mensagem.id} como lida.")
                mensagem.lida = True

                db.commit()
                db.refresh(mensagem)

            # ======================================
            # MONTA OS DADOS ATUALIZADOS DA MENSAGEM
            # ======================================

            mensagem_json = {
                "id": mensagem.id,
                "negociacao_id": mensagem.negociacao_id,
                "remetente_id": mensagem.remetente_id,
                "texto": mensagem.texto,
                "data_envio": mensagem.data_envio.isoformat(),
                "lida": mensagem.lida
            }

            # ======================================
            # ENVIA PARA AS CONEXÕES DO CHAT
            # ======================================

            for usuario_id, conexao in list(
                conexoes_chat.get(negociacao_id, [])
            ):

                try:

                    if usuario_id == remetente_id:

                        await conexao.send_json(
                            {
                                "tipo": "confirmacao_mensagem",
                                **mensagem_json
                            }
                        )

                    else:

                        await conexao.send_json(
                            mensagem_json
                        )

                except Exception as erro:

                    print(
                        f"❌ [WS Chat] Erro ao enviar mensagem para usuário {usuario_id}:",
                        erro
                    )

            # ======================================
            # NOTIFICA O OUTRO USUÁRIO
            # ======================================

            if outro_usuario_id in conexoes_usuarios:

                notificacao = {
                    "tipo": "nova_mensagem",
                    "negociacao_id": negociacao_id,
                    "remetente_id": remetente_id,
                    "texto": mensagem.texto,
                    "data_envio": mensagem.data_envio.isoformat(),
                    "lida": mensagem.lida
                }

                for conexao_usuario in list(
                    conexoes_usuarios[outro_usuario_id]
                ):

                    try:

                        await conexao_usuario.send_json(
                            notificacao
                        )

                    except Exception as erro:

                        print(
                            f"❌ [WS Chat] Erro ao enviar notificação geral para usuário {outro_usuario_id}:",
                            erro
                        )

            # ======================================
            # NOTIFICA O REMETENTE SOBRE A LEITURA
            # ======================================

            if destinatario_no_chat:

                notificacao_leitura = {
                    "tipo": "mensagens_lidas",
                    "negociacao_id": negociacao_id,
                    "leitor_id": outro_usuario_id,
                    "mensagem_ids": [mensagem.id]
                }

                if remetente_id in conexoes_usuarios:

                    for conexao_usuario in list(
                        conexoes_usuarios[remetente_id]
                    ):

                        try:

                            await conexao_usuario.send_json(
                                notificacao_leitura
                            )

                        except Exception as erro:

                            print(
                                f"❌ [WS Chat] Erro ao notificar leitura para remetente {remetente_id}:",
                                erro
                            )

    except WebSocketDisconnect:

        print(
            f"🔌 [WS Chat] WebSocket do chat desconectado. Negociação: {negociacao_id}, Usuário: {remetente_id}"
        )

    finally:

        db.close()

        # ======================================
        # REMOVE SOMENTE ESTA CONEXÃO
        # ======================================

        if negociacao_id in conexoes_chat:

            conexoes_chat[negociacao_id] = [
                (usuario_id, conexao)
                for usuario_id, conexao
                in conexoes_chat[negociacao_id]
                if conexao is not websocket
            ]

            if not conexoes_chat[negociacao_id]:
                del conexoes_chat[negociacao_id]
                print(f"🗑️ [WS Chat] Sala da negociação {negociacao_id} esvaziada e removida da memória.")
