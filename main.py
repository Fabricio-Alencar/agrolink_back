
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
    inspetor = inspect(engine)

    # Tabelas existentes antes da inicialização
    tabelas_antes = set(inspetor.get_table_names())

    print("\n========== BANCO DE DADOS AGROLINK ==========")

    # Criação das tabelas principais
    Base.metadata.create_all(bind=engine)

    # Criação das tabelas do chat
    ChatBase.metadata.create_all(bind=engine)

    # Tabelas existentes após a criação
    inspetor = inspect(engine)
    tabelas_depois = set(inspetor.get_table_names())

    # Identifica tabelas criadas e já existentes
    tabelas_criadas = tabelas_depois - tabelas_antes
    tabelas_existentes = tabelas_depois & tabelas_antes

    print("\n--- TABELAS PRINCIPAIS E DO CHAT ---")

    if tabelas_criadas:
        for tabela in sorted(tabelas_criadas):
            print(f"[CRIADA] {tabela}")
    else:
        print("[INFO] Nenhuma tabela nova foi criada.")

    if tabelas_existentes:
        for tabela in sorted(tabelas_existentes):
            print(f"[EXISTENTE] {tabela}")

    print("\n--- RESUMO ---")
    print(f"Total de tabelas: {len(tabelas_depois)}")
    print(f"Tabelas criadas: {len(tabelas_criadas)}")
    print(f"Tabelas que já existiam: {len(tabelas_existentes)}")

    print("============================================\n")

except Exception as e:
    print(f"[ERRO] Falha ao criar/verificar as tabelas: {e}")
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
    "https://agrol1nk-f6emc9brhkhseuds.brazilsouth-01.azurewebsites.net",
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