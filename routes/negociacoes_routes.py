from fastapi import APIRouter, Depends, HTTPException, status

from services import negociacoes_service
from auth.dependencies import get_current_user


router = APIRouter(tags=["Negociações"])


# =========================
# LISTAR NEGOCIAÇÕES DO MARKETPLACE
# =========================
@router.get("/negociacoes/{tipo_de_negociante}")
def listar_negociacoes(
    tipo_de_negociante: str,
    usuario_logado=Depends(get_current_user)
):

    user_id = usuario_logado["user_id"]

    try:
        negociacoes = negociacoes_service.listar_negociacoes(
            user_id,
            tipo_de_negociante
        )

        lista_final = []

        for p in negociacoes:

            if tipo_de_negociante.lower() == "produtor":
                parceiro = p.comprador
            else:
                parceiro = p.vendedor

            item = {
                "id": p.id,
                "quantidade": p.quantidade,
                "data_entrega": p.data_entrega.isoformat() if p.data_entrega else None,
                "descricao": p.descricao,
                "status": p.status,

                "produto_nome": p.produto.nome,
                "produto_descricao": p.produto.descricao,
                "produto_unidade": p.produto.unidade,
                "produto_foto": p.produto.foto,
                "produto_preco": p.produto.preco,

                "negociante_nome": parceiro.nome if parceiro else "N/A",
                "negociante_estado": parceiro.estado if parceiro else "N/A",
                "negociante_cidade": parceiro.cidade if parceiro else "N/A",
                "negociante_telefone": parceiro.telefone if parceiro else "N/A",
                "negociante_email": parceiro.email if parceiro else "N/A",
            }

            lista_final.append(item)

        return lista_final

    except Exception as e:
        print(f"[ERRO CRÍTICO] Falha na rota: {str(e)}")

        raise HTTPException(
            status_code=500,
            detail={
                "erro": f"Erro ao listar negociações: {str(e)}"
            }
        )


# =========================
# ATUALIZAR STATUS
# =========================
@router.put("/negociacoes/{id}/status")
def alterar_status(
    id: int,
    data: dict,
    usuario_logado=Depends(get_current_user)
):

    novo_status = data.get("status")

    if not novo_status:
        raise HTTPException(
            status_code=400,
            detail={
                "erro": "Status não fornecido"
            }
        )

    resultado, codigo_http = negociacoes_service.atualizar_status_negociacao(
        id,
        novo_status
    )

    if codigo_http >= 400:
        raise HTTPException(
            status_code=codigo_http,
            detail={
                "erro": resultado.get(
                    "erro",
                    "Erro ao atualizar status"
                )
            }
        )

    return resultado


# =========================
# CONFIRMAR ENTREGA/RECEBIMENTO
# =========================
@router.put("/negociacoes/{id}/confirmar")
def confirmar_acao(
    id: int,
    data: dict,
    usuario_logado=Depends(get_current_user)
):

    acao = data.get("acao")

    if not acao:
        raise HTTPException(
            status_code=400,
            detail={
                "erro": "Ação não fornecida"
            }
        )

    resultado, codigo_http = negociacoes_service.registrar_confirmacao_service(
        id,
        acao
    )

    if codigo_http >= 400:
        raise HTTPException(
            status_code=codigo_http,
            detail={
                "erro": resultado.get(
                    "erro",
                    "Erro ao registrar confirmação"
                )
            }
        )

    return resultado


# =========================
# DELETAR NEGOCIAÇÃO
# =========================
@router.delete("/negociacoes/{id}")
def deletar_negociacao(
    id: int,
    usuario_logado=Depends(get_current_user)
):

    user_id = usuario_logado["user_id"]

    resultado, codigo_http = negociacoes_service.deletar_negociacao_service(
        id,
        user_id
    )

    if codigo_http >= 400:
        raise HTTPException(
            status_code=codigo_http,
            detail={
                "erro": resultado.get(
                    "erro",
                    "Erro ao deletar negociação"
                )
            }
        )

    return resultado