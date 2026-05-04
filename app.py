from flask import Flask
from flask_cors import CORS  # permite requisições do frontend
from config import Config
from models import db

# =========================
# IMPORTAÇÃO DOS MODELS
# (necessário para criar tabelas)
# =========================
from models.usuario import Usuario
from models.produto import Produto
from models.negociacao import Negociacao

# =========================
# IMPORTAÇÃO DAS ROTAS
# =========================
from routes.produtos_routes import produtos_bp
from routes.auth_routes import auth_bp
from routes.marketplace_routes import marketplace_bp
from routes.negociacoes_routes import negociacoes_bp
# from routes.perfil_routes import perfil_bp


def create_app():
    app = Flask(__name__)

    # =========================
    # CONFIGURAÇÕES DO APP
    # =========================
    app.config.from_object(Config)

    # Configurações de Cookie para Cross-Origin (Sessão entre servidores)
    # SESSION_COOKIE_SAMESITE='None' permite enviar cookies entre domínios diferentes
    # SESSION_COOKIE_SECURE=True é obrigatório ao usar SameSite='None' (requer HTTPS)
    app.config.update(
        SESSION_COOKIE_SAMESITE='None',
        SESSION_COOKIE_SECURE=True
    )

    # =========================
    # CORS (permite requisições do frontend)
    # =========================
    CORS(
        app,
        supports_credentials=True,
        origins=[
            "http://127.0.0.1:5500",
            "http://127.0.0.1:8000",
            "https://front-agrolink-aff0bvbqd2buhfax.eastus-01.azurewebsites.net/",
            "https://front-agrolink-aff0bvbqd2buhfax.eastus-01.azurewebsites.net",
            "https://back-agrolink-bmbkepbbdkabdhhd.eastus-01.azurewebsites.net", 
            "https://agro-link.azurewebsites.net",
        ]
    )

    # =========================
    # INICIALIZA BANCO DE DADOS
    # =========================
    db.init_app(app)

    # =========================
    # REGISTRO DAS ROTAS
    # =========================
    app.register_blueprint(produtos_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(marketplace_bp)

    app.register_blueprint(negociacoes_bp)
    # app.register_blueprint(perfil_bp)

    # =========================
    # CRIA TABELAS NO BANCO
    # =========================
    with app.app_context():
        db.create_all()

    return app


# =========================
# INICIALIZA A APLICAÇÃO
# =========================
app = create_app()


# 🩺 Endpoint de verificação
@app.get("/")
def status():
    return {"status": "API está no ar 🚀"}

#if __name__ == "__main__":
    # debug=True reinicia o servidor automaticamente
#    app.run(debug=True)
