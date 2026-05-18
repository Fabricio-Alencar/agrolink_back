from flask import Blueprint, request, jsonify, session
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

    # 📦 busca produtos do usuário
    produtos = produto_service.listar_produtos_produtor(user_id)

    # 🔄 retorna JSON formatado
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

            # 📸 URL pública Azure Blob Storage
            "foto": p.foto
        }
        for p in produtos
    ]), 200


# =========================
# CRIAR PRODUTO (LOGADO)
# =========================
@produtos_bp.route('/produtos', methods=['POST'])
def criar_produto():

    # =========================
    # 1. CAPTURA DADOS
    # =========================
    data = request.form.to_dict()

    # captura arquivo enviado
    arquivo_foto = request.files.get('foto')

    # =========================
    # 2. VALIDA LOGIN
    # =========================
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({
            "erro": "Usuário não autenticado"
        }), 401

    # =========================
    # 3. VINCULA AO PRODUTOR
    # =========================
    data['produtor_id'] = user_id

    try:

        # =========================
        # 4. CRIA PRODUTO
        # =========================
        produto = produto_service.criar_produto(
            data,
            arquivo_foto
        )

        # =========================
        # 5. RESPOSTA
        # =========================
        return jsonify({
            "msg": "Produto criado com sucesso",

            "produto": {
                "id": produto.id,
                "nome": produto.nome,
                "preco": produto.preco,
                "descricao": produto.descricao,
                "foto": produto.foto
            }

        }), 201

    except Exception as e:

        return jsonify({
            "erro": str(e)
        }), 400


# =========================
# EXCLUIR PRODUTO
# =========================
@produtos_bp.route(
    '/produtos/<int:produto_id>',
    methods=['DELETE']
)
def excluir_produto(produto_id):

    # 🔐 usuário logado
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({
            "erro": "Usuário não autenticado"
        }), 401

    try:

        # remove produto
        produto_service.deletar_produto(
            produto_id,
            user_id
        )

        return jsonify({
            "msg": "Produto removido com sucesso",
            "id_excluido": produto_id
        }), 200

    except Exception as e:

        return jsonify({
            "erro": str(e)
        }), 403


# =========================
# ATUALIZAR PRODUTO
# =========================
@produtos_bp.route(
    '/produtos/<int:produto_id>',
    methods=['POST']
)
def atualizar_produto(produto_id):

    # 🔐 usuário logado
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({
            "erro": "Usuário não autenticado"
        }), 401

    # captura dados
    data = request.form.to_dict()

    # captura nova foto
    arquivo_foto = request.files.get('foto')

    try:

        # atualiza produto
        produto = produto_service.atualizar_produto(
            produto_id,
            user_id,
            data,
            arquivo_foto
        )

        return jsonify({

            "msg": "Produto atualizado com sucesso",

            "produto": {
                "id": produto.id,
                "nome": produto.nome,
                "foto": produto.foto
            }

        }), 200

    except Exception as e:

        return jsonify({
            "erro": str(e)
        }), 400
