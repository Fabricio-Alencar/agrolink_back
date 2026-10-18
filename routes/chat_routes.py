
import os

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
# IDENTIFICAÇÃO DO PROCESSO / INSTÂNCIA
# =========================================================

def identificar_processo():
    return (
        f"instancia={os.getenv('WEBSITE_INSTANCE_ID', 'local')} "
        f"pid={os.getpid()}"
    )


# =========================================================
# AUTENTICAR WEBSOCKET
# =========================================================

def autenticar_websocket(websocket):

    access_token = websocket.cookies.get("access_token")

    print(
        f"[WS AUTH] Cookie access_token recebido: "
        f"{access_token is not None}"
    )

    if not access_token:
        print("[WS AUTH] Falha: cookie não recebido.")
        return None

    try:

        payload = decodificar_token(access_token)

        user_id = payload.get("sub")
        tipo = payload.get("tipo")

        if not user_id or not tipo:
            print("[WS AUTH] Falha: token sem sub ou tipo.")
            return None

        db = SessionLocal()

        try:

            usuario = db.get(
                Usuario,
                int(user_id)
            )

            if not usuario:
                print(
                    f"[WS AUTH] Falha: usuário {user_id} não encontrado."
                )
                return None

            print(
                f"[WS AUTH] Autenticado: usuário={usuario.id}, "
                f"tipo={usuario.tipo}"
            )

            return {
                "user_id": usuario.id,
                "tipo": usuario.tipo,
                "nome": usuario.nome
            }

        finally:
            db.close()

    except Exception as erro:

        print(
            f"[WS AUTH] Erro ao validar token: "
            f"{type(erro).__name__}: {erro}"
        )

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

    conversa = buscar_conversa(
        db,
        dados.negociacao_id
    )

    if not conversa:
        raise HTTPException(
            status_code=409,
            detail=(
                "Inicie a conversa pelo botão Conversar "
                "antes de enviar mensagens."
            )
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

    conversa = buscar_conversa(
        db,
        negociacao_id
    )

    if not conversa:
        raise HTTPException(
            status_code=404,
            detail="Esta conversa ainda não foi iniciada."
        )

    mensagens_lidas = marcar_mensagens_como_lidas(
        db,
        negociacao_id,
        usuario_id
    )

    if negociacao.comprador_id == usuario_id:
        outro_usuario_id = negociacao.vendedor_id
    else:
        outro_usuario_id = negociacao.comprador_id

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
                        "[WS LEITURA] Erro ao notificar leitura:",
                        type(erro).__name__,
                        erro
                    )

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
        f"[WS GERAL] Tentativa de conexão recebida. "
        f"{identificar_processo()}"
    )

    usuario = autenticar_websocket(websocket)

    if not usuario:

        print(
            "[WS GERAL] Conexão recusada: autenticação falhou."
        )

        await websocket.close(code=1008)
        return

    usuario_id = usuario["user_id"]

    await websocket.accept()

    if usuario_id not in conexoes_usuarios:
        conexoes_usuarios[usuario_id] = []

    conexoes_usuarios[usuario_id].append(websocket)

    print(
        f"[WS GERAL] Conectado: usuário={usuario_id}; "
        f"{identificar_processo()}; "
        f"conexoes_usuario={len(conexoes_usuarios[usuario_id])}"
    )

    try:

        await websocket.send_json({
            "tipo": "conexao",
            "mensagem": "WebSocket geral conectado."
        })

        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:

        print(
            f"[WS GERAL] Desconectado: usuário={usuario_id}; "
            f"{identificar_processo()}"
        )

    except Exception as erro:

        print(
            f"[WS GERAL] Erro: {type(erro).__name__}: {erro}; "
            f"{identificar_processo()}"
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


# =========================================================
# WEBSOCKET DO CHAT
# =========================================================

@router.websocket("/ws/{negociacao_id}")
async def chat_websocket(
    websocket: WebSocket,
    negociacao_id: int
):

    print(
        f"[WS CHAT] Tentativa: negociação={negociacao_id}; "
        f"{identificar_processo()}"
    )

    usuario = autenticar_websocket(websocket)

    if not usuario:

        print("[WS CHAT] Recusado: autenticação falhou.")
        await websocket.close(code=1008)
        return

    remetente_id = usuario["user_id"]

    negociacao = buscar_negociacao(negociacao_id)

    if not negociacao:

        print("[WS CHAT] Recusado: negociação não encontrada.")
        await websocket.close(code=1008)
        return

    if not usuario_tem_acesso(negociacao, remetente_id):

        print("[WS CHAT] Recusado: usuário sem acesso.")
        await websocket.close(code=1008)
        return

    db = SessionChat()

    try:

        conversa = buscar_conversa(
            db,
            negociacao_id
        )

        if not conversa:

            print("[WS CHAT] Recusado: conversa não iniciada.")
            await websocket.close(code=1008)
            return

        await websocket.accept()

        if negociacao_id not in conexoes_chat:
            conexoes_chat[negociacao_id] = []

        conexoes_chat[negociacao_id].append(
            (remetente_id, websocket)
        )

        print(
            f"[WS DIAGNOSTICO] Conexão registrada; "
            f"{identificar_processo()} "
            f"negociação={negociacao_id} "
            f"usuário={remetente_id} "
            f"usuarios_registrados="
            f"{[uid for uid, _ in conexoes_chat[negociacao_id]]}"
        )

        while True:

            texto = await websocket.receive_text()

            print(
                f"[WS RECEBIMENTO] Mensagem recebida; "
                f"{identificar_processo()} "
                f"negociação={negociacao_id} "
                f"remetente={remetente_id}"
            )

            mensagem = criar_mensagem(
                db,
                negociacao_id,
                remetente_id,
                texto
            )

            if negociacao.comprador_id == remetente_id:
                outro_usuario_id = negociacao.vendedor_id
            else:
                outro_usuario_id = negociacao.comprador_id

            conexoes_atuais = list(
                conexoes_chat.get(negociacao_id, [])
            )

            destinatario_no_chat = any(
                uid == outro_usuario_id
                for uid, _ in conexoes_atuais
            )

            if destinatario_no_chat:

                mensagem.lida = True
                db.commit()
                db.refresh(mensagem)

            mensagem_json = {
                "id": mensagem.id,
                "negociacao_id": mensagem.negociacao_id,
                "remetente_id": mensagem.remetente_id,
                "texto": mensagem.texto,
                "data_envio": mensagem.data_envio.isoformat(),
                "lida": mensagem.lida
            }

            print(
                f"[WS BROADCAST] Preparando envio; "
                f"{identificar_processo()} "
                f"negociação={negociacao_id} "
                f"remetente={remetente_id} "
                f"destinatario={outro_usuario_id} "
                f"usuarios_conectados="
                f"{[uid for uid, _ in conexoes_atuais]}"
            )

            for usuario_id, conexao in conexoes_atuais:

                try:

                    if usuario_id == remetente_id:

                        await conexao.send_json({
                            "tipo": "confirmacao_mensagem",
                            **mensagem_json
                        })

                    else:

                        await conexao.send_json(mensagem_json)

                    print(
                        f"[WS BROADCAST] Envio concluído; "
                        f"negociação={negociacao_id} "
                        f"destinatario_socket_usuario={usuario_id}"
                    )

                except Exception as erro:

                    print(
                        f"[WS BROADCAST] Falha ao enviar; "
                        f"negociação={negociacao_id} "
                        f"socket_usuario={usuario_id} "
                        f"erro={type(erro).__name__}: {erro}"
                    )

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
                        await conexao_usuario.send_json(notificacao)

                    except Exception as erro:
                        print(
                            "[WS NOTIFICACAO] Falha ao notificar "
                            f"usuário={outro_usuario_id}: "
                            f"{type(erro).__name__}: {erro}"
                        )

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
                                "[WS LEITURA] Falha ao notificar "
                                f"remetente={remetente_id}: "
                                f"{type(erro).__name__}: {erro}"
                            )

    except WebSocketDisconnect:

        print(
            f"[WS CHAT] Desconectado: negociação={negociacao_id}, "
            f"usuário={remetente_id}; {identificar_processo()}"
        )

    except Exception as erro:

        print(
            f"[WS CHAT] Erro: {type(erro).__name__}: {erro}; "
            f"negociação={negociacao_id}; "
            f"usuário={remetente_id}; {identificar_processo()}"
        )

    finally:

        db.close()

        if negociacao_id in conexoes_chat:

            conexoes_chat[negociacao_id] = [
                (usuario_id, conexao)
                for usuario_id, conexao
                in conexoes_chat[negociacao_id]
                if conexao is not websocket
            ]

            if not conexoes_chat[negociacao_id]:
                del conexoes_chat[negociacao_id]

            print(
                f"[WS CHAT] Conexão removida; "
                f"{identificar_processo()} "
                f"negociação={negociacao_id} "
                f"usuarios_restantes="
                f"{[uid for uid, _ in conexoes_chat.get(negociacao_id, [])]}"
            )
