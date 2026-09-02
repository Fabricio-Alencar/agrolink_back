from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from services import marketplace_service
from auth.dependencies import get_current_user


router = APIRouter(tags=["Marketplace"])


# =========================
# LISTAR PRODUTOS DO MARKETPLACE (LOGADO)
# =========================
@router.get("/produtos")
def produtos(usuario_logado=Depends(get_current_user)):

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
                "produtor_nome": p.produtor.nome,
                "produtor_estado": p.produtor.estado,
                "produtor_cidade": p.produtor.cidade,
                "produtor_avaliacao": p.produtor.avaliacao or 5.0
            }
            for p in produtos
        ]

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "erro": f"Erro ao listar produtos: {str(e)}"
            }
        )


# =========================
# REGISTRAR PEDIDO (LOGADO)
# =========================
@router.post("/negociar", status_code=status.HTTP_201_CREATED)
def criar_negociacao(
    data: dict,
    usuario_logado=Depends(get_current_user)
):

    comprador_id = usuario_logado["user_id"]

    try:
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
        return JSONResponse(
            status_code=400,
            content={
                "erro": str(e)
            }
        )