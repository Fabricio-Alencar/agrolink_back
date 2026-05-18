from models import db
from models.produto import Produto
from models.usuario import Usuario

# Serviço responsável pelo upload para Azure Blob Storage
from services.upload_service import upload_imagem_azure


# =========================
# BUSCA TODOS OS PRODUTOS DE UM PRODUTOR ESPECÍFICO
# =========================
def listar_produtos_produtor(user_id):
    """
    Retorna todos os produtos pertencentes
    ao produtor informado.
    """
    return Produto.query.filter_by(produtor_id=user_id).all()


# =========================
# CRIAR PRODUTO
# =========================
def criar_produto(data, arquivo_foto):

    # =========================
    # 1. VALIDA USUÁRIO
    # =========================
    # Verifica se o usuário existe
    usuario = Usuario.query.get(data['produtor_id'])

    if not usuario:
        raise Exception("Usuário não encontrado")

    # Apenas produtores podem cadastrar produtos
    if usuario.tipo != 'produtor':
        raise Exception("Apenas produtores podem criar produtos")

    # =========================
    # 2. PROCESSA FOTO
    # =========================
    # Caso o usuário não envie imagem,
    # usamos uma imagem padrão online.
    caminho_foto_banco = (
        "https://via.placeholder.com/300x300.png?text=Sem+Imagem"
    )

    # Se existir arquivo de imagem:
    if arquivo_foto:

        # Faz upload da imagem para Azure Blob Storage
        # e retorna a URL pública da imagem
        caminho_foto_banco = upload_imagem_azure(arquivo_foto)

    # =========================
    # 3. CRIA PRODUTO
    # =========================
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

            # 📸 Agora salvamos URL pública da Azure
            foto=caminho_foto_banco,
        )

        # adiciona no banco
        db.session.add(produto)

        # confirma alterações
        db.session.commit()

        print(f"✅ SUCESSO: Produto {produto.id} cadastrado.")

        return produto

    except Exception as e:

        # desfaz alterações pendentes
        db.session.rollback()

        print("\n❌ [ERRO NO BANCO DE DADOS]")
        print(f"Detalhes do erro: {str(e)}")

        raise Exception(f"Erro ao salvar no banco: {str(e)}")


# =========================
# DELETAR PRODUTO
# =========================
def deletar_produto(produto_id, user_id):

    # =========================
    # 1. BUSCA PRODUTO
    # =========================
    produto = Produto.query.get(produto_id)

    if produto:
        print("Produto encontrado:", produto.nome)
        print("ID do dono:", produto.produtor_id)
        print("Foto:", produto.foto)
    else:
        print("Produto NÃO encontrado")

    # valida existência
    if not produto:
        raise Exception("Produto não encontrado")

    # =========================
    # 2. SEGURANÇA
    # =========================
    # Apenas o dono pode excluir
    if produto.produtor_id != user_id:
        raise Exception(
            "Você não tem permissão para excluir este produto"
        )

    # =========================
    # 3. REMOVE DO BANCO
    # =========================
    try:

        # remove produto
        db.session.delete(produto)

        # confirma exclusão
        db.session.commit()

        print("✅ Produto deletado com sucesso")

        return True

    except Exception as e:

        db.session.rollback()

        print("❌ Erro ao deletar:", str(e))

        raise Exception("Erro ao excluir no banco de dados")


# =========================
# ATUALIZAR PRODUTO
# =========================
def atualizar_produto(produto_id, user_id, data, arquivo_foto):

    # =========================
    # 1. BUSCA PRODUTO
    # =========================
    produto = Produto.query.get(produto_id)

    # valida existência
    if not produto:
        raise Exception("Produto não encontrado")

    # =========================
    # 2. SEGURANÇA
    # =========================
    # Apenas o dono pode editar
    if produto.produtor_id != user_id:
        raise Exception(
            "Você não tem permissão para editar este produto"
        )

    # =========================
    # 3. ATUALIZA CAMPOS
    # =========================
    produto.nome = data.get('nome', produto.nome)
    produto.preco = data.get('preco', produto.preco)
    produto.quantidade = data.get('quantidade', produto.quantidade)
    produto.unidade = data.get('unidade', produto.unidade)
    produto.categoria = data.get('categoria', produto.categoria)
    produto.descricao = data.get('descricao', produto.descricao)
    produto.status = data.get('status', produto.status)

    # =========================
    # 4. PROCESSA NOVA FOTO
    # =========================
    # Se o usuário enviar uma nova imagem:
    if arquivo_foto:

        # Faz upload da nova imagem para Azure
        # e substitui URL antiga
        produto.foto = upload_imagem_azure(arquivo_foto)

    # =========================
    # 5. SALVA ALTERAÇÕES
    # =========================
    try:

        # confirma alterações
        db.session.commit()

        print("✅ Produto atualizado")

        return produto

    except Exception as e:

        db.session.rollback()

        print("❌ Erro ao atualizar:", str(e))

        raise Exception(
            f"Erro ao atualizar banco: {str(e)}"
        )
