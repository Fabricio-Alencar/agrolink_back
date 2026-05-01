from flask import Blueprint, request, jsonify, session
from services import marketplace_service
from models import Produto
from models import Negociacao
from models import db
from datetime import datetime


marketplace_bp = Blueprint('marketplace', __name__)

# =========================
# LISTAR PRODUTOS DO MARKETPLACE (LOGADO)
# =========================
@marketplace_bp.route('/produtos', methods=['GET'])
def produtos():
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"erro": "Usuário não autenticado"}), 401

    try:
        produtos = marketplace_service.listar_produtos()

        return jsonify([
            {
                "id": p.id,
                "nome": p.nome,
                "preco": p.preco,
                "quantidade": p.quantidade,
                "unidade": p.unidade,
                "categoria": p.categoria,
                "descricao": p.descricao,
                "foto": p.foto,
                "status": p.status,
                # 👤 Dados do Produtor extraídos via backref
                "produtor_nome": p.produtor.nome,
                "produtor_estado": p.produtor.estado,
                "produtor_cidade": p.produtor.cidade,
                "produtor_avaliacao": p.produtor.avaliacao or 5.0 # Caso seja nulo
            }
            for p in produtos
        ]), 200

    except Exception as e:
        return jsonify({"erro": f"Erro ao listar produtos: {str(e)}"}), 500
    

# =========================
# REGISTRAR PEDIDO (LOGADO)
# =========================
@marketplace_bp.route('/negociar', methods=['POST'])
def criar_negociacao():
    # 1. Identifica o comprador pela sessão
    comprador_id = session.get("user_id")
    if not comprador_id:
        return jsonify({"erro": "Faça login para negociar"}), 401

    # 2. Pega os dados do JSON enviado pelo modal.js
    data = request.get_json()

    try:
        # 3. Processa a negociação
        negociacao = marketplace_service.registrar_pedido(comprador_id, data)

        return jsonify({
            "msg": "Solicitação de negociação enviada!",
            "id": negociacao.id,
            "status": negociacao.status
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": str(e)}), 400