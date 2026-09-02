from fastapi import APIRouter, Depends, HTTPException, status

from services import marketplace_service
from auth.dependencies import get_current_user


router = APIRouter(tags=["Marketplace"])


# =========================
# LISTAR PRODUTOS DO MARKETPLACE (LOGADO)
# =========================
@router.get("/produtos")
def produtos(usuario_logado=Depends(get_current_user)):

    # pega usuário logado
    user_id = usuario_logado["user_id"]

    try:
        produtos = marketplace_service.listar_produtos()

        return [
            {
                "id": p.id,
                "nome": p.nome,
                "preco": p.preco,
                "quantidade": p.quantidade,
                "unidade": p.unidade,
                "categoria": p.categoria,
                "descricao": p.descricao,
                "foto": p.foto,
                "status": p.status,

                # Dados do Produtor extraídos via relacionamento
                "produtor_nome": p.produtor.nome,
                "produtor_estado": p.produtor.estado,
                "produtor_cidade": p.produtor.cidade,
                "produtor_avaliacao": p.produtor.avaliacao or 5.0 # Caso seja nulo
            }
            for p in produtos
        ]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao listar produtos: {str(e)}"
        )


# =========================
# REGISTRAR PEDIDO (LOGADO)
# =========================
@router.post("/negociar", status_code=status.HTTP_201_CREATED)
def criar_negociacao(
    data: dict,
    usuario_logado=Depends(get_current_user)
):

    # 1. Identifica o comprador pelo usuário logado
    comprador_id = usuario_logado["user_id"]

    try:
        # 2. Processa a negociação
        negociacao = marketplace_service.registrar_pedido(
            comprador_id,
            data
        )

        return {
            "msg": "Solicitação de negociação enviada!",
            "id": negociacao.id,
            "status": negociacao.status
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
