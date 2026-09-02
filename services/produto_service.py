from uuid import uuid4
from sqlalchemy import select
from database import SessionLocal
from models.produto import Produto
from models.usuario import Usuario
from services.azure_storage_service import (
    upload_arquivo,
    deletar_arquivo,
    CONTAINER_PRODUTOS
)

def listar_produtos_produtor(user_id):
    db = SessionLocal()
    try:
        resultado = db.execute(
            select(Produto).where(Produto.produtor_id == user_id)
        )
        return resultado.scalars().all()
    finally:
        db.close()

def criar_produto(data, arquivo_foto):
    db = SessionLocal()
    try:
        usuario = db.get(Usuario, data['produtor_id'])
        if not usuario:
            raise Exception("Usuário não encontrado")
        if usuario.tipo != 'produtor':
            raise Exception("Apenas produtores podem criar produtos")

        nome_blob = None
        if arquivo_foto:
            extensao = ""
            if arquivo_foto.filename and "." in arquivo_foto.filename:
                extensao = "." + arquivo_foto.filename.rsplit(".", 1)[1].lower()

            nome_blob = f"{uuid4().hex}{extensao}"

            upload_arquivo(
                arquivo_foto.file,
                nome_blob,
                CONTAINER_PRODUTOS
            )

        caminho_foto_banco = nome_blob if nome_blob else "foto_generica.png"

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
            print(f"✅ SUCESSO: Produto {produto.id} cadastrado.")
            return produto
        except Exception as e:
            db.rollback()
            print("\n❌ [ERRO NO BANCO DE DADOS]:")
            print(f"Detalhes do erro: {str(e)}")
            if nome_blob:
                try:
                    deletar_arquivo(
                        nome_blob,
                        CONTAINER_PRODUTOS
                    )
                except Exception as erro_blob:
                    print(
                        "⚠️ Não foi possível remover o Blob após erro no banco:",
                        str(erro_blob)
                    )
            raise Exception(f"Erro ao salvar no banco: {str(e)}")
    finally:
        db.close()

def deletar_produto(produto_id, user_id):
    db = SessionLocal()
    try:
        produto = db.get(Produto, produto_id)
        if produto:
            print("Produto encontrado:", produto.nome)
            print("ID do dono do produto:", produto.produtor_id)
            print("Foto salva:", produto.foto)
        else:
            print("Produto NÃO encontrado")

        if not produto:
            raise Exception("Produto não encontrado")

        if produto.produtor_id != user_id:
            raise Exception("Você não tem permissão para excluir este produto")

        foto_produto = produto.foto

        if (
            foto_produto
            and foto_produto != "foto_generica.png"
            and not foto_produto.startswith("http://")
            and not foto_produto.startswith("https://")
        ):
            try:
                deletar_arquivo(
                    foto_produto,
                    CONTAINER_PRODUTOS
                )
                print(f"🗑️ Foto do produto {produto_id} removida do Azure.")
            except Exception as e:
                print("⚠️ Não foi possível excluir a foto do produto:", str(e))

        try:
            db.delete(produto)
            db.commit()
            print(f"✅ SUCESSO: Produto {produto_id} deletado.")
            return True
        except Exception as e:
            db.rollback()
            print("❌ Erro ao deletar produto:", str(e))
            raise Exception("Erro ao excluir no banco de dados")
    finally:
        db.close()

def atualizar_produto(produto_id, user_id, data, arquivo_foto):
    db = SessionLocal()
    try:
        produto = db.get(Produto, produto_id)
        if not produto:
            raise Exception("Produto não encontrado")

        if produto.produtor_id != user_id:
            raise Exception("Você não tem permissão para editar este produto")

        foto_antiga = produto.foto

        produto.nome = data.get('nome', produto.nome)
        produto.preco = data.get('preco', produto.preco)
        produto.quantidade = data.get('quantidade', produto.quantidade)
        produto.unidade = data.get('unidade', produto.unidade)
        produto.categoria = data.get('categoria', produto.categoria)
        produto.descricao = data.get('descricao', produto.descricao)
        produto.status = data.get('status', produto.status)

        if arquivo_foto:
            extensao = ""
            if arquivo_foto.filename and "." in arquivo_foto.filename:
                extensao = "." + arquivo_foto.filename.rsplit(".", 1)[1].lower()

            novo_nome_blob = f"{uuid4().hex}{extensao}"

            upload_arquivo(
                arquivo_foto.file,
                novo_nome_blob,
                CONTAINER_PRODUTOS
            )

            produto.foto = novo_nome_blob

            if (
                foto_antiga
                and foto_antiga != "foto_generica.png"
                and not foto_antiga.startswith("http://")
                and not foto_antiga.startswith("https://")
            ):
                try:
                    deletar_arquivo(
                        foto_antiga,
                        CONTAINER_PRODUTOS
                    )
                    print(f"🗑️ Foto antiga do produto {produto_id} removida do Azure.")
                except Exception as e:
                    print("⚠️ Não foi possível excluir a foto antiga:", str(e))

        try:
            db.commit()
            db.refresh(produto)
            print(f"✅ SUCESSO: Produto {produto_id} atualizado.")
            return produto
        except Exception as e:
            db.rollback()
            if arquivo_foto and 'novo_nome_blob' in locals():
                try:
                    deletar_arquivo(
                        novo_nome_blob,
                        CONTAINER_PRODUTOS
                    )
                except Exception as erro_blob:
                    print(
                        "⚠️ Não foi possível remover o novo Blob após erro no banco:",
                        str(erro_blob)
                    )
            raise Exception(f"Erro ao atualizar banco: {str(e)}")
    finally:
        db.close()