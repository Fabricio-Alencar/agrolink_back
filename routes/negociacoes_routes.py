from flask import Blueprint, request, jsonify, session
from services import negociacoes_service

negociacoes_bp = Blueprint('negociacoes', __name__)

# =========================
# LISTAR NEGOCIAÇÕES DO MARKETPLACE
# =========================
@negociacoes_bp.route('/negociacoes/<string:tipo_de_negociante>', methods=['GET'])
def listarNegociacoes(tipo_de_negociante):
    # 🔐 pega usuário logado da sessão Flask
    user_id = session.get("user_id")

    # 🚨 bloqueia acesso se não estiver logado
    if not user_id:
        return jsonify({"erro": "Usuário não autenticado"}), 401


    try:
        # Busca a lista de objetos Negociacao no service
        negociacoes = negociacoes_service.listar_negociacoes(user_id, tipo_de_negociante)

        lista_final = []
        
        for p in negociacoes:
            # LÓGICA DO NEGOCIANTE:
            # Se eu estou logado como produtor, a pessoa com quem eu falo é o comprador.
            # Se eu estou logado como estabelecimento, a pessoa com quem eu falo é o vendedor.
            if tipo_de_negociante.lower() == "produtor":
                parceiro = p.comprador  # 'comprador' vem do backref no ARQUIVO 3
            else:
                parceiro = p.vendedor   # 'vendedor' vem do backref no ARQUIVO 3

            # Montagem do dicionário para o JSON
            item = {
                "id": p.id,
                "quantidade": p.quantidade,
                "data_entrega": p.data_entrega.isoformat() if p.data_entrega else None,
                "descricao": p.descricao,
                "status": p.status,

                # Produto (usa o backref='produto' do ARQUIVO 2)
                "produto_nome": p.produto.nome,
                "produto_descricao": p.produto.descricao,
                "produto_unidade": p.produto.unidade,
                "produto_foto": p.produto.foto,
                "produto_preco": p.produto.preco,

                # Negociante (dados do parceiro de negócio identificado acima)
                "negociante_nome": parceiro.nome if parceiro else "N/A",
                "negociante_estado": parceiro.estado if parceiro else "N/A",
                "negociante_cidade": parceiro.cidade if parceiro else "N/A",
                "negociante_telefone": parceiro.telefone if parceiro else "N/A",
                "negociante_email": parceiro.email if parceiro else "N/A",

            }
            lista_final.append(item)

        return jsonify(lista_final), 200

    except Exception as e:
        print(f"[ERRO CRÍTICO] Falha na rota: {str(e)}")
        return jsonify({"erro": f"Erro ao listar negociações: {str(e)}"}), 500
    
    # =========================
# ATUALIZAR STATUS
# =========================
@negociacoes_bp.route('/negociacoes/<int:id>/status', methods=['PUT'])
def alterar_status(id):
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"erro": "Usuário não autenticado"}), 401

    dados = request.get_json()
    novo_status = dados.get('status')
    
    if not novo_status:
        return jsonify({"erro": "Status não fornecido"}), 400
        
    resultado, codigo_http = negociacoes_service.atualizar_status_negociacao(id, novo_status)
    return jsonify(resultado), codigo_http

# =========================
# CONFIRMAR ENTREGA/RECEBIMENTO
# =========================
@negociacoes_bp.route('/negociacoes/<int:id>/confirmar', methods=['PUT'])
def confirmar_acao(id):
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"erro": "Usuário não autenticado"}), 401

    dados = request.get_json()
    acao = dados.get('acao')
    
    if not acao:
        return jsonify({"erro": "Ação não fornecida"}), 400
        
    resultado, codigo_http = negociacoes_service.registrar_confirmacao_service(id, acao)
    return jsonify(resultado), codigo_http

# =========================
# DELETAR NEGOCIAÇÃO (Oculta ou apaga do BD)
# =========================
@negociacoes_bp.route('/negociacoes/<int:id>', methods=['DELETE'])
def deletar_negociacao(id):
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"erro": "Usuário não autenticado"}), 401

    resultado, codigo_http = negociacoes_service.deletar_negociacao_service(id, user_id)
    return jsonify(resultado), codigo_http