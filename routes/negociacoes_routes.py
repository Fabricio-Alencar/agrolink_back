from fastapi import APIRouter, Depends, HTTPException, status

from services import negociacoes_service, avaliacoes_service
from database import SessionLocal
from services.azure_storage_service import (
    gerar_url_sas,
    CONTAINER_PRODUTOS
)
from auth.dependencies import get_current_user


router = APIRouter(tags=["Negociações"])


# =========================
# CAMPOS PARA ACOMPANHAR O PEDIDO E A AVALIAÇÃO
# =========================
def dados_de_avaliacao(negociacoes):
    """Busca de uma vez as avaliações dos pedidos e a média dos produtores."""
    db = SessionLocal()

    try:
        avaliacoes = avaliacoes_service.avaliacoes_das_negociacoes(
            db, [n.id for n in negociacoes]
        )
        resumos = avaliacoes_service.resumo_avaliacoes(
            db, [n.vendedor_id for n in negociacoes]
        )
    finally:
        db.close()

    return avaliacoes, resumos


def campos_de_acompanhamento(negociacao, avaliacoes, resumos):
    """Campos usados pelo front na linha do tempo e no modal de avaliação."""
    resumo = resumos.get(negociacao.vendedor_id, {})

    return {
        "data_criacao": (
            negociacao.data_criacao.isoformat()
            if negociacao.data_criacao
            else None
        ),
        "data_atualizacao": (
            negociacao.data_atualizacao.isoformat()
            if negociacao.data_atualizacao
            else None
        ),
        "entrega_confirmada": bool(negociacao.entrega_confirmada),
        "recebimento_confirmado": bool(negociacao.recebimento_confirmado),

        # Produtor do pedido (para abrir o perfil público dele)
        "produtor_id": negociacao.vendedor_id,
        "produtor_avaliacao": resumo.get("media"),  # None = sem avaliações
        "produtor_total_avaliacoes": resumo.get("total", 0),

        # None = pedido ainda não avaliado
        "avaliacao": avaliacoes_service.avaliacao_para_json(
            avaliacoes.get(negociacao.id)
        ),
    }


# =========================
# BUSCAR UMA NEGOCIAÇÃO ESPECÍFICA
# =========================
@router.get("/negociacoes/detalhes/{id}")
def buscar_negociacao_detalhes(
    id: int,
    usuario_logado=Depends(get_current_user)
):

    user_id = usuario_logado["user_id"]

    # =========================
    # BUSCA A NEGOCIAÇÃO
    # =========================

    negociacao = (
        negociacoes_service.buscar_negociacao(
            id
        )
    )

    if not negociacao:

        raise HTTPException(
            status_code=404,
            detail={
                "erro": "Negociação não encontrada"
            }
        )

    # =========================
    # VERIFICA ACESSO
    # =========================

    if (
        negociacao.comprador_id != user_id
        and
        negociacao.vendedor_id != user_id
    ):

        raise HTTPException(
            status_code=403,
            detail={
                "erro": "Você não possui acesso a esta negociação."
            }
        )

    # =========================
    # IDENTIFICA O OUTRO PARTICIPANTE
    # =========================

    if negociacao.comprador_id == user_id:

        parceiro = negociacao.vendedor

    else:

        parceiro = negociacao.comprador

    # =========================
    # RETORNA OS DADOS
    # =========================

    return {

        "id": negociacao.id,

        "quantidade": negociacao.quantidade,

        "data_entrega": (
            negociacao.data_entrega.isoformat()
            if negociacao.data_entrega
            else None
        ),

        "descricao": negociacao.descricao,

        "status": negociacao.status,

        **campos_de_acompanhamento(
            negociacao,
            *dados_de_avaliacao([negociacao])
        ),

        # =========================
        # PRODUTO
        # =========================

        "produto_nome": (
            negociacao.produto.nome
            if negociacao.produto
            else "Produto"
        ),

        "produto_descricao": (
            negociacao.produto.descricao
            if negociacao.produto
            else None
        ),

        "produto_unidade": (
            negociacao.produto.unidade
            if negociacao.produto
            else None
        ),

        "produto_preco": (
            negociacao.produto.preco
            if negociacao.produto
            else None
        ),

        "produto_foto": (
            gerar_url_sas(
                CONTAINER_PRODUTOS,
                negociacao.produto.foto
            )
            if negociacao.produto
            and negociacao.produto.foto
            and negociacao.produto.foto != "foto_generica.png"
            and "uploads/produtos/foto_generica.png"
            not in negociacao.produto.foto
            else None
        ),

        # =========================
        # OUTRO PARTICIPANTE
        # =========================

        "negociante_nome": (
            parceiro.nome
            if parceiro
            else "N/A"
        ),

        "negociante_estado": (
            parceiro.estado
            if parceiro and not parceiro.conta_excluida
            else "N/A"
        ),

        "negociante_cidade": (
            parceiro.cidade
            if parceiro and not parceiro.conta_excluida
            else "N/A"
        ),

        "negociante_telefone": (
            parceiro.telefone
            if parceiro and not parceiro.conta_excluida
            else "N/A"
        ),

        "negociante_email": (
            parceiro.email
            if parceiro and not parceiro.conta_excluida
            else "N/A"
        ),

        # Conta excluída: o front mostra a etiqueta "Conta excluída"
        "negociante_conta_excluida": bool(parceiro and parceiro.conta_excluida)
    }


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

        avaliacoes, resumos = dados_de_avaliacao(negociacoes)

        for p in negociacoes:

            if tipo_de_negociante.lower() == "produtor":

                parceiro = p.comprador

            else:

                parceiro = p.vendedor

            item = {

                "id": p.id,

                "quantidade": p.quantidade,

                "data_entrega": (
                    p.data_entrega.isoformat()
                    if p.data_entrega
                    else None
                ),

                "descricao": p.descricao,

                "status": p.status,

                **campos_de_acompanhamento(p, avaliacoes, resumos),

                "produto_nome": p.produto.nome,

                "produto_descricao": p.produto.descricao,

                "produto_unidade": p.produto.unidade,

                "produto_foto": (
                    gerar_url_sas(
                        CONTAINER_PRODUTOS,
                        p.produto.foto
                    )
                    if p.produto.foto
                    and p.produto.foto != "foto_generica.png"
                    and "uploads/produtos/foto_generica.png"
                    not in p.produto.foto
                    else None
                ),

                "produto_preco": p.produto.preco,

                "negociante_nome": (
                    parceiro.nome
                    if parceiro
                    else "N/A"
                ),

                "negociante_estado": (
                    parceiro.estado
                    if parceiro and not parceiro.conta_excluida
                    else "N/A"
                ),

                "negociante_cidade": (
                    parceiro.cidade
                    if parceiro and not parceiro.conta_excluida
                    else "N/A"
                ),

                "negociante_telefone": (
                    parceiro.telefone
                    if parceiro and not parceiro.conta_excluida
                    else "N/A"
                ),

                "negociante_email": (
                    parceiro.email
                    if parceiro and not parceiro.conta_excluida
                    else "N/A"
                ),

                # Conta excluída: o front mostra a etiqueta "Conta excluída"
                "negociante_conta_excluida": bool(parceiro and parceiro.conta_excluida)
            }

            lista_final.append(
                item
            )

        return lista_final

    except Exception as e:

        print(
            f"[ERRO CRÍTICO] Falha na rota: {str(e)}"
        )

        raise HTTPException(
            status_code=500,
            detail={
                "erro":
                    f"Erro ao listar negociações: {str(e)}"
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

    resultado, codigo_http = (
        negociacoes_service.atualizar_status_negociacao(
            id,
            novo_status,
            usuario_logado["user_id"]
        )
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

    resultado, codigo_http = (
        negociacoes_service.registrar_confirmacao_service(
            id,
            acao,
            usuario_logado["user_id"]
        )
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

    resultado, codigo_http = (
        negociacoes_service.deletar_negociacao_service(
            id,
            user_id
        )
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
