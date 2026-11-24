
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy import inspect, text

# ==========================================
# IMPORTAÇÃO DO BANCO DE DADOS
# ==========================================

from database import Base, engine
from chat_database import ChatBase

# ==========================================
# IMPORTAÇÃO DOS MODELOS PRINCIPAIS
# ==========================================
from models.usuario import Usuario
from models.produto import Produto
from models.negociacao import Negociacao
from models.avaliacao import Avaliacao

# ==========================================
# IMPORTAÇÃO DOS MODELOS DO CHAT
# ==========================================

from models.mensagem import Mensagem
from models.conversa import Conversa

# ==========================================
# IMPORTAÇÃO DAS ROTAS
# ==========================================

from routes.auth_routes import router as auth_router
from routes.perfil_routes import router as perfil_router
from routes.produtos_routes import router as produtos_router
from routes.marketplace_routes import router as marketplace_router
from routes.negociacoes_routes import router as negociacoes_router
from routes.chat_routes import router as chat_router
from routes.avaliacoes_routes import router as avaliacoes_router

# ==========================================
# CRIAÇÃO DA APLICAÇÃO
# ==========================================

app = FastAPI(title="AgroLink API")

# ==========================================
# CRIAÇÃO DAS TABELAS
# ==========================================

try:
    # Cria todas as tabelas dos modelos principais.
    # Inclui usuarios, produtos, negociacoes, avaliacoes etc.
    Base.metadata.create_all(bind=engine)

    print("[OK] Tabelas principais verificadas/criadas.")

    # Cria as tabelas do sistema de chat.
    ChatBase.metadata.create_all(bind=engine)

    print("[OK] Tabelas do chat verificadas/criadas.")

except Exception as e:
    print(f"[ERRO] Falha ao criar as tabelas: {e}")
    raise

# ==========================================
# ATUALIZAÇÃO DA TABELA NEGOCIACOES
# ==========================================

try:
    colunas = [
        coluna["name"]
        for coluna in inspect(engine).get_columns("negociacoes")
    ]

    if "data_atualizacao" not in colunas:
        with engine.begin() as conexao:
            conexao.execute(
                text(
                    "ALTER TABLE negociacoes "
                    "ADD COLUMN data_atualizacao TIMESTAMP"
                )
            )

        print("[OK] Coluna negociacoes.data_atualizacao criada.")

    else:
        print("[OK] Coluna negociacoes.data_atualizacao já existe.")

except Exception as e:
    print(
        f"[AVISO] Não foi possível verificar/criar "
        f"negociacoes.data_atualizacao: {e}"
    )

# ==========================================
# CONFIGURAÇÃO DO CORS
# ==========================================

origins = [
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:8000",
    "http://127.0.0.1:8000",

    # Adicione aqui as quatro URLs do Azure
    # que você já utilizava na configuração anterior.
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# REGISTRO DAS ROTAS
# ==========================================

app.include_router(auth_router)
app.include_router(perfil_router)
app.include_router(produtos_router)
app.include_router(marketplace_router)
app.include_router(negociacoes_router)
app.include_router(chat_router)
app.include_router(avaliacoes_router)

# ==========================================
# ROTA INICIAL
# ==========================================

@app.get("/")
def home():
    return {"message": "AgroLink API funcionando!"}
