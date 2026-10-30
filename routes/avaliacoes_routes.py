from fastapi import APIRouter, Depends, HTTPException

from services import avaliacoes_service
from services.azure_storage_service import (
    gerar_url_sas,
    CONTAINER_PRODUTOS,
    CONTAINER_USUARIOS
)
from auth.dependencies import get_current_user


router = APIRouter(tags=["Avaliações"])


# =========================
# AVALIAR PRODUTOR (0,5 A 5 ESTRELAS + COMENTÁRIO)
# =========================
@router.post("/negociacoes/{id}/avaliar")
def avaliar_produtor(
    id: int,
    data: dict,
    usuario_logado=Depends(get_current_user)
):

    resultado, codigo_http = avaliacoes_service.avaliar_produtor(
        id,
        usuario_logado["user_id"],
        data.get("nota"),
        data.get("comentario")
    )

    if codigo_http >= 400:

        raise HTTPException(
            status_code=codigo_http,
            detail={
                "erro": resultado.get(
                    "erro",
                    "Erro ao registrar avaliação"
                )
            }
        )

    return resultado


# =========================
# PERFIL PÚBLICO DO PRODUTOR (LOGADO)
# =========================
@router.get("/produtores/{id}")
def perfil_produtor(
    id: int,
    usuario_logado=Depends(get_current_user)
):

    perfil = avaliacoes_service.perfil_publico_produtor(id)

    if not perfil:

        raise HTTPException(
            status_code=404,
            detail={
                "erro": "Produtor não encontrado"
            }
        )

    produtor = perfil["produtor"]

    # Telefone e e-mail ficam de fora: o contato acontece pelo pedido/chat
    return {

        "id": produtor.id,

        "nome": produtor.nome,

        # Conta excluída: o perfil mostra a etiqueta "Conta excluída"
        "conta_excluida": bool(produtor.conta_excluida),

        "cidade": produtor.cidade,

        "estado": produtor.estado,

        "foto_perfil": (
            gerar_url_sas(
                CONTAINER_USUARIOS,
                produtor.foto_perfil
            )
            if produtor.foto_perfil
            and "user.webp" not in produtor.foto_perfil
            else None
        ),

        # None = "Sem avaliações"
        "media_avaliacoes": perfil["media"],

        "total_avaliacoes": perfil["total_avaliacoes"],

        "distribuicao": perfil["distribuicao"],

        "avaliacoes": perfil["avaliacoes"],

        "produtos": [
            {
                "id": p.id,
                "nome": p.nome,
                "preco": p.preco,
                "unidade": p.unidade,
                "categoria": p.categoria,
                "foto": (
                    gerar_url_sas(
                        CONTAINER_PRODUTOS,
                        p.foto
                    )
                    if p.foto
                    and p.foto != "foto_generica.png"
                    and "uploads/produtos/foto_generica.png"
                    not in p.foto
                    else None
                ),
            }
            for p in perfil["produtos"]
        ]
    }
