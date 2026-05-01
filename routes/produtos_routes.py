from flask import Blueprint, request, jsonify, session, url_for
from services import produto_service

produtos_bp = Blueprint('produtos', __name__)

# =========================
# MEUS PRODUTOS (LOGADO)
# =========================
@produtos_bp.route('/meus-produtos', methods=['GET'])
def meus_produtos():

    # 🔐 pega usuário logado da sessão Flask
    user_id = session.get("user_id")

    # 🚨 bloqueia acesso se não estiver logado
    if not user_id:
        return jsonify({"erro": "Usuário não autenticado"}), 401

    # 📦 busca produtos do usuário no service
    produtos = produto_service.listar_produtos_produtor(user_id)

    # 🔄 retorna em JSON formatado para o front
    return jsonify([
        {
            "id": p.id,
            "nome": p.nome,
            "preco": p.preco,
            "quantidade": p.quantidade,
            "unidade": p.unidade,
            "categoria": p.categoria,
            "descricao": p.descricao,
            "status": p.status,
            "foto": url_for('static', filename=p.foto) if p.foto else None
        }
        for p in produtos
    ]), 200


# =========================
# CRIAR PRODUTO (LOGADO)
# =========================
@produtos_bp.route('/produtos', methods=['POST'])
def criar_produto():

    # 1. CAPTURA DADOS DO FRONT (Ajustado para receber Multipart/FormData)
    # request.form captura todos os textos do JS
    data = request.form.to_dict()
    
    # request.files captura o arquivo físico da foto
    arquivo_foto = request.files.get('foto')

    # 2. VERIFICA USUÁRIO LOGADO
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"erro": "Usuário não autenticado"}), 401

    # 3. VINCULA PRODUTO AO USUÁRIO
    data['produtor_id'] = user_id

    try:

        # 4. CRIA NO SERVICE (Passando os textos e o arquivo da foto)
        produto = produto_service.criar_produto(data, arquivo_foto)

        # 5. RESPOSTA PARA FRONT
        return jsonify({
            "msg": "Produto criado com sucesso",
            "produto": {
                "id": produto.id,
                "nome": produto.nome,
                "preco": produto.preco,
                "descricao": produto.descricao
            }
        }), 201

    except Exception as e:
        return jsonify({
            "erro": str(e)
        }), 400    
    

# =========================
# EXCLUIR PRODUTO (LOGADO)
# =========================
@produtos_bp.route('/produtos/<int:produto_id>', methods=['DELETE'])
def excluir_produto(produto_id):
    # 1. VERIFICA USUÁRIO LOGADO
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"erro": "Usuário não autenticado"}), 401

    try:
        # 2. CHAMA O SERVICE (Passando o ID do produto e do dono)
        produto_service.deletar_produto(produto_id, user_id)

        # 3. RESPOSTA DE SUCESSO
        return jsonify({
            "msg": "Produto removido com sucesso",
            "id_excluido": produto_id
        }), 200

    except Exception as e:
        # Caso o produto não exista ou não pertença ao usuário
        return jsonify({
            "erro": str(e)
        }), 403
    

# =========================
# ATUALIZAR PRODUTO (LOGADO)
# =========================
@produtos_bp.route('/produtos/<int:produto_id>', methods=['POST']) # Usando POST para facilitar o envio de Multipart
def atualizar_produto(produto_id):
    # 1. VERIFICA USUÁRIO LOGADO
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"erro": "Usuário não autenticado"}), 401

    # 2. CAPTURA DADOS E FOTO
    data = request.form.to_dict()
    arquivo_foto = request.files.get('foto')

    try:
        # 3. CHAMA O SERVICE
        produto = produto_service.atualizar_produto(produto_id, user_id, data, arquivo_foto)

        return jsonify({
            "msg": "Produto atualizado com sucesso",
            "produto": {"id": produto.id, "nome": produto.nome}
        }), 200

    except Exception as e:
        return jsonify({"erro": str(e)}), 400   
    
