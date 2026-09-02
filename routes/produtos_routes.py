from fastapi import APIRouter, Depends, Form, UploadFile, File, status
from fastapi.responses import JSONResponse

from services import produto_service
from auth.dependencies import get_current_user


router = APIRouter(tags=["Produtos"])


# =========================
# MEUS PRODUTOS (LOGADO)
# =========================
@router.get("/meus-produtos")
def meus_produtos(usuario_logado=Depends(get_current_user)):

    # pega usuário logado
    user_id = usuario_logado["user_id"]

    try:
        # busca produtos do usuário
        produtos = produto_service.listar_produtos_produtor(user_id)

        # retorna JSON formatado
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

                # URL pública Azure Blob Storage
                "foto": p.foto
            }
            for p in produtos
        ]

    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={
                "erro": str(e)
            }
        )


# =========================
# CRIAR PRODUTO (LOGADO)
# =========================
@router.post("/produtos", status_code=status.HTTP_201_CREATED)
def criar_produto(
    usuario_logado=Depends(get_current_user),

    nome: str = Form(...),
    preco: float = Form(...),
    quantidade: float = Form(...),
    unidade: str = Form(...),
    categoria: str = Form(...),
    descricao: str = Form(...),
    status_produto: str = Form(...), # status_produto: str = Form(..., alias="status"),
    foto: UploadFile | None = File(default=None)
):

    # =========================
    # 1. PEGA USUÁRIO LOGADO
    # =========================
    user_id = usuario_logado["user_id"]

    # =========================
    # 2. MONTA OS DADOS
    # =========================
    data = {
        "nome": nome,
        "preco": preco,
        "quantidade": quantidade,
        "unidade": unidade,
        "categoria": categoria,
        "descricao": descricao,
        "status": status_produto,

        # vincula ao produtor logado
        "produtor_id": user_id
    }

    try:

        # =========================
        # 3. CRIA PRODUTO
        # =========================
        produto = produto_service.criar_produto(
            data,
            foto
        )

        # =========================
        # 4. RESPOSTA
        # =========================
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
            content={
                "erro": str(e)
            }
        )


# =========================
# EXCLUIR PRODUTO
# =========================
@router.delete("/produtos/{produto_id}")
def excluir_produto(
    produto_id: int,
    usuario_logado=Depends(get_current_user)
):

    # usuário logado
    user_id = usuario_logado["user_id"]

    try:

        # remove produto
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
            content={
                "erro": str(e)
            }
        )


# =========================
# ATUALIZAR PRODUTO
# =========================
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
    status_produto: str | None = Form(default=None, alias="status"),

    foto: UploadFile | None = File(default=None)
):

    # usuário logado
    user_id = usuario_logado["user_id"]

    # captura dados
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

        # atualiza produto
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
            content={
                "erro": str(e)
            }
        )