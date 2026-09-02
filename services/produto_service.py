from uuid import uuid4

from sqlalchemy import select

from database import SessionLocal
from models.produto import Produto
from models.usuario import Usuario

from services.azure_storage_service import (
    upload_arquivo,
    CONTAINER_PRODUTOS
)


# =========================
# BUSCA TODOS OS PRODUTOS DE UM PRODUTOR ESPECÍFICO
# =========================
def listar_produtos_produtor(user_id):
    db = SessionLocal()

    try:
        resultado = db.execute(
            select(Produto).where(Produto.produtor_id == user_id)
        )

        return resultado.scalars().all()

    finally:
        db.close()


# =========================
# CRIAR PRODUTO - RECEBE DADOS + ARQUIVO DE FOTO
# =========================
def criar_produto(data, arquivo_foto):
    db = SessionLocal()

    try:
        # 1. VERIFICA SE O PRODUTOR EXISTE E É DO TIPO CORRETO
        usuario = db.get(Usuario, data['produtor_id'])

        if not usuario:
            raise Exception("Usuário não encontrado")

        if usuario.tipo != 'produtor':
            raise Exception("Apenas produtores podem criar produtos")

        # 2. PROCESSA A FOTO
        # Se nenhuma foto for enviada, usa a foto genérica.
        nome_blob = None

        if arquivo_foto:
            # Pega a extensão da imagem
            extensao = ""

            if arquivo_foto.filename and "." in arquivo_foto.filename:
                extensao = "." + arquivo_foto.filename.rsplit(
                    ".", 1
                )[1].lower()

            # Gera um nome único
            nome_blob = f"{uuid4().hex}{extensao}"

            # Envia diretamente para o Azure Blob Storage
            upload_arquivo(
                arquivo_foto.file,
                nome_blob,
                CONTAINER_PRODUTOS
            )

        # Se não enviou imagem, mantém a foto genérica
        caminho_foto_banco = (
            nome_blob
            if nome_blob
            else "foto_generica.png"
        )

        # 3. CRIA O PRODUTO NO BANCO DE DADOS
        try:
            produto = Produto(
                nome=data.get('nome'),
                preco=data.get('preco'),
                produtor_id=data.get('produtor_id'),
                quantidade=data.get('quantidade'),
                status=data.get('status'),
                categoria=data.get('categoria'),
                unidade=data.get('unidade'),
                descricao=data.get('descricao'),
                foto=caminho_foto_banco
            )

            db.add(produto)
            db.commit()
            db.refresh(produto)

            print(
                f"✅ SUCESSO: Produto {produto.id} cadastrado."
            )

            return produto

        except Exception as e:
            db.rollback()

            print("\n❌ [ERRO NO BANCO DE DADOS]:")
            print(f"Detalhes do erro: {str(e)}")

            raise Exception(
                f"Erro ao salvar no banco: {str(e)}"
            )

    finally:
        db.close()


# =========================
# DELETAR PRODUTO
# =========================
def deletar_produto(produto_id, user_id):
    db = SessionLocal()

    try:
        # 1. BUSCA O PRODUTO NO BANCO
        produto = db.get(Produto, produto_id)

        if produto:
            print("Produto encontrado:", produto.nome)
            print("ID do dono do produto:", produto.produtor_id)
            print("Foto salva:", produto.foto)
        else:
            print("Produto NÃO encontrado")

        if not produto:
            raise Exception("Produto não encontrado")

        # Segurança: só o dono pode excluir
        if produto.produtor_id != user_id:
            raise Exception(
                "Você não tem permissão para excluir este produto"
            )

        try:
            # 2. REMOVE DO BANCO
            db.delete(produto)

            # 3. POR ENQUANTO NÃO REMOVEMOS A IMAGEM DO AZURE
            #
            # A exclusão do Blob Storage será implementada
            # no próximo passo.

            # 4. CONFIRMA A EXCLUSÃO NO BANCO
            db.commit()

            print("Produto deletado com sucesso")

            return True

        except Exception as e:
            db.rollback()

            print("Erro ao deletar:", str(e))

            raise Exception(
                "Erro ao excluir no banco de dados"
            )

    finally:
        db.close()


# =========================
# ATUALIZAR PRODUTO
# =========================
def atualizar_produto(
    produto_id,
    user_id,
    data,
    arquivo_foto
):
    db = SessionLocal()

    try:
        # 1. BUSCA O PRODUTO E VALIDA DONO
        produto = db.get(Produto, produto_id)

        if not produto:
            raise Exception("Produto não encontrado")

        if produto.produtor_id != user_id:
            raise Exception(
                "Você não tem permissão para editar este produto"
            )

        # 2. ATUALIZA CAMPOS DE TEXTO
        produto.nome = data.get(
            'nome',
            produto.nome
        )

        produto.preco = data.get(
            'preco',
            produto.preco
        )

        produto.quantidade = data.get(
            'quantidade',
            produto.quantidade
        )

        produto.unidade = data.get(
            'unidade',
            produto.unidade
        )

        produto.categoria = data.get(
            'categoria',
            produto.categoria
        )

        produto.descricao = data.get(
            'descricao',
            produto.descricao
        )

        produto.status = data.get(
            'status',
            produto.status
        )

        # 3. PROCESSA NOVA FOTO
        if arquivo_foto:

            # Pega a extensão da imagem
            extensao = ""

            if arquivo_foto.filename and "." in arquivo_foto.filename:
                extensao = "." + arquivo_foto.filename.rsplit(
                    ".", 1
                )[1].lower()

            # Gera nome único
            nome_blob = f"{uuid4().hex}{extensao}"

            # Envia nova imagem para o Azure
            upload_arquivo(
                arquivo_foto.file,
                nome_blob,
                CONTAINER_PRODUTOS
            )

            # Atualiza o nome do Blob no banco
            produto.foto = nome_blob

        # 4. SALVA NO BANCO
        try:
            db.commit()
            db.refresh(produto)

            return produto

        except Exception as e:
            db.rollback()

            raise Exception(
                f"Erro ao atualizar banco: {str(e)}"
            )

    finally:
        db.close()