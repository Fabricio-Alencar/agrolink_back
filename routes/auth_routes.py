from flask import Blueprint, request, jsonify, session
from services.usuario_service import criar_usuario, login_usuario

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/cadastro", methods=["POST"])
def cadastro():
    data = request.json
    try:
        usuario = criar_usuario(data)
        # Retornamos sucesso. O JS lerá isso e fará o redirecionamento.
        return jsonify({
            "msg": "Usuário criado com sucesso",
            "proxima_pagina": "/login" # Opcional: enviar a rota desejada aqui
        }), 201
    except Exception as e:
        return jsonify({"erro": str(e)}), 400

# =========================
# LOGIN
# =========================
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.json

    try:
        usuario = login_usuario(data)

        # 🔥 sessão (usuário logado)
        session["user_id"] = usuario.id
        session["tipo"] = usuario.tipo
        session["nome"] = usuario.nome

        return jsonify({
            "msg": "Login realizado",
            "user_id": usuario.id,
            "tipo": usuario.tipo
        })

    except Exception as e:
        return jsonify({"erro": str(e)}), 401

@auth_bp.route("/session", methods=["GET"])
def get_session():
    if "user_id" not in session:
        return jsonify({
            "logado": False
        })

    return jsonify({
        "logado": True,
        "user_id": session.get("user_id"),
        "tipo": session.get("tipo"),
        "nome": session.get("nome")
    })
