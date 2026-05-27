from flask import Blueprint, request, jsonify, session
from services import perfil_service

perfil_bp = Blueprint('perfil', __name__)

# =========================
# BUSCAR DADOS DO PERFIL (LOGADO)
# =========================
@perfil_bp.route('/perfil', methods=['GET'])
def obter_perfil():
    # 1. VERIFICA USUÁRIO LOGADO
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"erro": "Usuário não autenticado"}), 401

    try:
        # 2. CHAMA O SERVICE
        usuario = perfil_service.obter_perfil_usuario(user_id)

        # 3. RETORNA DADOS FORMATADOS PARA O FRONT
        return jsonify({
            "nome": usuario.nome,
            "email": usuario.email,
            "telefone": usuario.telefone,
            "cidade": usuario.cidade,
            "estado": usuario.estado,
            "foto_perfil": getattr(usuario, 'foto_perfil', 'assets/user.webp'),
            "tipo": usuario.tipo
        }), 200

    except Exception as e:
        return jsonify({"erro": str(e)}), 400


# =========================
# ATUALIZAR PERFIL E FOTO (LOGADO)
# =========================
@perfil_bp.route('/perfil', methods=['POST']) # Usamos POST por causa do envio de Multipart/FormData da imagem
def atualizar_perfil():
    # 1. VERIFICA USUÁRIO LOGADO
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"erro": "Usuário não autenticado"}), 401

    # 2. CAPTURA DADOS E FOTO (Igual feito em produtos_routes.py)
    data = request.form.to_dict()
    arquivo_foto = request.files.get('foto')

    try:
        # 3. CHAMA O SERVICE
        usuario = perfil_service.atualizar_perfil_usuario(user_id, data, arquivo_foto)

        # Atualiza o nome na sessão caso o usuário tenha alterado no perfil
        session["nome"] = usuario.nome
        session["foto_perfil"] = getattr(usuario, 'foto_perfil', 'assets/user.webp')

        return jsonify({
            "msg": "Perfil atualizado com sucesso",
            "foto_perfil": getattr(usuario, 'foto_perfil', 'assets/user.webp')
        }), 200

    except Exception as e:
        return jsonify({"erro": str(e)}), 400


# =========================
# EXCLUIR CONTA (LOGADO)
# =========================
@perfil_bp.route('/perfil', methods=['DELETE'])
def excluir_conta():
    # 1. VERIFICA USUÁRIO LOGADO
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"erro": "Usuário não autenticado"}), 401

    try:
        # 2. CHAMA O SERVICE
        perfil_service.excluir_conta_usuario(user_id)

        # 3. LIMPA A SESSÃO LOGO APÓS A EXCLUSÃO
        session.clear() 

        return jsonify({
            "msg": "Conta excluída com sucesso"
        }), 200

    except Exception as e:
        return jsonify({"erro": str(e)}), 400