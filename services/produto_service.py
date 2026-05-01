import os
from uuid import uuid4
from models import db
from models.produto import Produto
from models.usuario import Usuario

# 📂 Caminho da pasta onde as fotos serão salvas fisicamente
UPLOAD_FOLDER = os.path.join('static', 'uploads', 'produtos')


# =========================
# BUSCA TODOS OS PRODUTOS DE UM PRODUTOR ESPECÍFICO 
# =========================
def listar_produtos_produtor(user_id):
    return Produto.query.filter_by(produtor_id=user_id).all()



# =========================
# CRIAR PRODUTO - RECEBE DADOS + ARQUIVO DE FOTO
# =========================
def criar_produto(data, arquivo_foto):
    # 1. VERIFICA SE O PRODUTOR EXISTE E É DO TIPO CORRETO
    usuario = Usuario.query.get(data['produtor_id'])
    if not usuario:
        raise Exception("Usuário não encontrado")
    if usuario.tipo != 'produtor':
        raise Exception("Apenas produtores podem criar produtos")

    # 2. PROCESSA A FOTO (se enviada) E GERA O CAMINHO PARA O BANCO
    caminho_foto_banco = "uploads/produtos/foto_generica.png" # Foto padrão se não enviar nada
    if arquivo_foto:
        # Garante que a pasta física existe no servidor
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        # Pega a extensão da imagem (ex: .jpg, .png)
        extensao = os.path.splitext(arquivo_foto.filename)[1]
        # Gera um nome único aleatório para não sobrescrever arquivos
        nome_arquivo = f"{uuid4().hex}{extensao}"  
        # Salva o arquivo na pasta
        caminho_completo = os.path.join(UPLOAD_FOLDER, nome_arquivo)
        arquivo_foto.save(caminho_completo)
        # Define a string que será guardada no banco de dados
        caminho_foto_banco = f"uploads/produtos/{nome_arquivo}"

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
            foto=caminho_foto_banco, # 📸 Salva o caminho gerado acima
        )
        db.session.add(produto)
        db.session.commit()
        print(f"✅ SUCESSO: Produto {produto.id} cadastrado.")
        return produto

    except Exception as e:
        # Se algo der errado no banco, desfazemos qualquer alteração pendente
        db.session.rollback()
        # 🧹 Limpeza: Apaga a foto caso o banco falhe, para não acumular lixo
        if arquivo_foto and caminho_foto_banco != "uploads/produtos/foto_generica.png":
            arquivo_lixo = os.path.join('static', caminho_foto_banco)
            if os.path.exists(arquivo_lixo):
                os.remove(arquivo_lixo)
        # Exibe o erro detalhado no terminal
        print("\n❌ [ERRO NO BANCO DE DADOS]:")
        print(f"Detalhes do erro: {str(e)}")        
        raise Exception(f"Erro ao salvar no banco: {str(e)}")
    



# =========================
# DELETAR PRODUTO 
# =========================
def deletar_produto(produto_id, user_id):
    # 1. BUSCA O PRODUTO NO BANCO
    produto = Produto.query.get(produto_id)

    if produto:
        print("Produto encontrado:", produto.nome)
        print("ID do dono do produto:", produto.produtor_id)
        print("Foto salva:", produto.foto)
    else:
        print("Produto NÃO encontrado")

    if not produto:
        raise Exception("Produto não encontrado")

    # 🔥 Segurança: só o dono pode excluir
    if produto.produtor_id != user_id:
        raise Exception("Você não tem permissão para excluir este produto")

    try:
        # 2. REMOVE DO BANCO (mas ainda não confirma, para garantir que a imagem só seja apagada se o banco aceitar)
        db.session.delete(produto)
        # 3. REMOVE IMAGEM DO DISCO
        if produto.foto and "foto_generica" not in produto.foto:
            caminho_imagem = produto.foto
            # Se vier só o caminho relativo, garante base correta
            if not caminho_imagem.startswith("static"):
                caminho_imagem = os.path.join('static', caminho_imagem)
            if os.path.exists(caminho_imagem):
                os.remove(caminho_imagem)
                print("Imagem removida com sucesso")
            else:
                print("Imagem NÃO encontrada no disco")

        # 4. CONFIRMA A EXCLUSÃO NO BANCO
        db.session.commit()
        print("Produto deletado com sucesso")
        return True

    except Exception as e:
        db.session.rollback()
        print("Erro ao deletar:", str(e))
        raise Exception("Erro ao excluir no banco de dados") 


# =========================
# ATUALIZAR PRODUTO
# =========================
def atualizar_produto(produto_id, user_id, data, arquivo_foto):
    # 1. BUSCA O PRODUTO E VALIDA DONO
    produto = Produto.query.get(produto_id)
    
    if not produto:
        raise Exception("Produto não encontrado")
    
    if produto.produtor_id != user_id:
        raise Exception("Você não tem permissão para editar este produto")

    # 2. ATUALIZA CAMPOS DE TEXTO
    produto.nome = data.get('nome', produto.nome)
    produto.preco = data.get('preco', produto.preco)
    produto.quantidade = data.get('quantidade', produto.quantidade)
    produto.unidade = data.get('unidade', produto.unidade)
    produto.categoria = data.get('categoria', produto.categoria)
    produto.descricao = data.get('descricao', produto.descricao)
    produto.status = data.get('status', produto.status)

    # 3. PROCESSA NOVA FOTO (SE HOUVER)
    if arquivo_foto:
        # a) Apagar a foto antiga do disco (se não for a genérica)
        if produto.foto and "foto_generica.png" not in produto.foto:
            caminho_antigo = os.path.join('static', produto.foto)
            if os.path.exists(caminho_antigo):
                os.remove(caminho_antigo)

        # b) Salvar a nova foto
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        extensao = os.path.splitext(arquivo_foto.filename)[1]
        nome_arquivo = f"{uuid4().hex}{extensao}"
        caminho_completo = os.path.join(UPLOAD_FOLDER, nome_arquivo)
        arquivo_foto.save(caminho_completo)
        
        # c) Atualiza o caminho no objeto produto
        produto.foto = f"uploads/produtos/{nome_arquivo}"

    # 4. SALVA NO BANCO
    try:
        db.session.commit()
        return produto
    except Exception as e:
        db.session.rollback()
        raise Exception(f"Erro ao atualizar banco: {str(e)}")       