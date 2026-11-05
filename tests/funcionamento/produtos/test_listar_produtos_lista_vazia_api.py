# O que estamos testando?
# 1. Um produtor autenticado consegue acessar sua listagem mesmo sem produtos?
# 2. A API retorna HTTP 200?
# 3. A API retorna uma lista vazia quando não existem produtos cadastrados?
# 4. O sistema trata corretamente a ausência de registros?


def test_listar_produtos_sem_cadastro(cliente_api):
    # Cadastrar produtor
    cadastro = cliente_api.post("/cadastro", json={
        "nome": "Produtor Sem Produtos",
        "email": "produtor_vazio@teste.com",
        "senha": "Senha123!",
        "tipo": "produtor"
    })

    assert cadastro.status_code == 201

    # Fazer login
    login = cliente_api.post("/login", json={
        "email": "produtor_vazio@teste.com",
        "senha": "Senha123!"
    })

    assert login.status_code == 200

    # Consultar produtos
    resposta = cliente_api.get("/meus-produtos")

    assert resposta.status_code == 200
    assert resposta.json() == []
    