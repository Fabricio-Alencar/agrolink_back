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

    # 🔐 pega usuário logado
    user_id = usuario_logado["user_id"]

    try:
        # Busca a lista de objetos Negociacao no service
        negociacoes = negociacoes_service.listar_negociacoes(
            user_id,
            tipo_de_negociante
        )

        lista_final = []

        for p in negociacoes:

            # LÓGICA DO NEGOCIANTE:
            # Se eu estou logado como produtor, a pessoa com quem eu falo é o comprador.
            # Se eu estou logado como estabelecimento, a pessoa com quem eu falo é o vendedor.
            if tipo_de_negociante.lower() == "produtor":
                parceiro = p.comprador
            else:
                parceiro = p.vendedor

            # Montagem do dicionário para o JSON
            item = {
                "id": p.id,
                "quantidade": p.quantidade,
                "data_entrega": p.data_entrega.isoformat() if p.data_entrega else None,
                "descricao": p.descricao,
                "status": p.status,

                # Produto
                "produto_nome": p.produto.nome,
                "produto_descricao": p.produto.descricao,
                "produto_unidade": p.produto.unidade,
                "produto_foto": p.produto.foto,
                "produto_preco": p.produto.preco,

                # Negociante (dados do parceiro de negócio identificado acima)
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
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao listar negociações: {str(e)}"
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
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status não fornecido"
        )

    resultado, codigo_http = negociacoes_service.atualizar_status_negociacao(
        id,
        novo_status
    )

    if codigo_http >= 400:
        raise HTTPException(
            status_code=codigo_http,
            detail=resultado.get("erro", "Erro ao atualizar status")
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
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ação não fornecida"
        )

    resultado, codigo_http = negociacoes_service.registrar_confirmacao_service(
        id,
        acao
    )

    if codigo_http >= 400:
        raise HTTPException(
            status_code=codigo_http,
            detail=resultado.get("erro", "Erro ao registrar confirmação")
        )

    return resultado


# =========================
# DELETAR NEGOCIAÇÃO (Oculta ou apaga do BD)
# =========================
@router.delete("/negociacoes/{id}")
def deletar_negociacao(
    id: int,
    usuario_logado=Depends(get_current_user)
):

    # usuário logado
    user_id = usuario_logado["user_id"]

    resultado, codigo_http = negociacoes_service.deletar_negociacao_service(
        id,
        user_id
    )

    if codigo_http >= 400:
        raise HTTPException(
            status_code=codigo_http,
            detail=resultado.get("erro", "Erro ao deletar negociação")
        )

    return resultado