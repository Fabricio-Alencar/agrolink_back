from fastapi import APIRouter, Depends, Form, UploadFile, File, status
from fastapi.responses import JSONResponse

from services import produto_service
from services.azure_storage_service import (
    gerar_url_sas,
    CONTAINER_PRODUTOS
)
from auth.dependencies import get_current_user


router = APIRouter(tags=["Produtos"])


@router.get("/meus-produtos")
def meus_produtos(usuario_logado=Depends(get_current_user)):
    user_id = usuario_logado["user_id"]

    try:
        produtos = produto_service.listar_produtos_produtor(user_id)

        return [
            {
                "id": p.id,
                "nome": p.nome,
                "preco": p.preco,
                "quantidade": p.quantidade,
                "unidade": p.unidade,
                "categoria": p.categoria,
                "descricao": p.descricao,
                "status": p.status,
                "foto": (
                    gerar_url_sas(
                        CONTAINER_PRODUTOS,
                        p.foto
                    )
                    if p.foto
                    and p.foto != "foto_generica.png"
                    and "uploads/produtos/foto_generica.png" not in p.foto
                    else None
                )
            }
            for p in produtos
        ]

    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"erro": str(e)}
        )


@router.post("/produtos", status_code=status.HTTP_201_CREATED)
def criar_produto(
    usuario_logado=Depends(get_current_user),
    nome: str = Form(...),
    preco: float = Form(...),
    quantidade: float = Form(...),
    unidade: str = Form(...),
    categoria: str = Form(...),
    descricao: str = Form(...),
    status_produto: str = Form(...),
    foto: UploadFile | None = File(default=None)
):
    user_id = usuario_logado["user_id"]

    data = {
        "nome": nome,
        "preco": preco,
        "quantidade": quantidade,
        "unidade": unidade,
        "categoria": categoria,
        "descricao": descricao,
        "status": status_produto,
        "produtor_id": user_id
    }

    try:
        produto = produto_service.criar_produto(
            data,
            foto
        )

        return {
            "msg": "Produto criado com sucesso",
            "produto": {
                "id": produto.id,
                "nome": produto.nome,
                "preco": produto.preco,
                "descricao": produto.descricao,
                "foto": produto.foto
            }
        }

    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"erro": str(e)}
        )


@router.delete("/produtos/{produto_id}")
def excluir_produto(
    produto_id: int,
    usuario_logado=Depends(get_current_user)
):
    user_id = usuario_logado["user_id"]

    try:
        produto_service.deletar_produto(
            produto_id,
            user_id
        )

        return {
            "msg": "Produto removido com sucesso",
            "id_excluido": produto_id
        }

    except Exception as e:
        return JSONResponse(
            status_code=403,
            content={"erro": str(e)}
        )


@router.post("/produtos/{produto_id}")
def atualizar_produto(
    produto_id: int,
    usuario_logado=Depends(get_current_user),
    nome: str | None = Form(default=None),
    preco: float | None = Form(default=None),
    quantidade: float | None = Form(default=None),
    unidade: str | None = Form(default=None),
    categoria: str | None = Form(default=None),
    descricao: str | None = Form(default=None),
    status_produto: str | None = Form(
        default=None,
        alias="status"
    ),
    foto: UploadFile | None = File(default=None)
):
    user_id = usuario_logado["user_id"]

    data = {
        "nome": nome,
        "preco": preco,
        "quantidade": quantidade,
        "unidade": unidade,
        "categoria": categoria,
        "descricao": descricao,
        "status": status_produto
    }

    try:
        produto = produto_service.atualizar_produto(
            produto_id,
            user_id,
            data,
            foto
        )

        return {
            "msg": "Produto atualizado com sucesso",
            "produto": {
                "id": produto.id,
                "nome": produto.nome,
                "foto": produto.foto
            }
        }

    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"erro": str(e)}
        )