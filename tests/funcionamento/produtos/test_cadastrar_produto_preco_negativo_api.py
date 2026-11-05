# O que estamos testando?
# 1. A API impede o cadastro de produtos com preço negativo?
# 2. A API retorna um código HTTP de erro?
# 3. O sistema impede valores financeiros inválidos?
# 4. Um produto com preço negativo deixa de ser cadastrado?


def test_impedir_cadastro_produto_com_preco_negativo(cliente_api):
    # Cadastrar produtor
    cadastro = cliente_api.post("/cadastro", json={
        "nome": "Produtor Teste",
        "email": "produtor_preco_negativo@teste.com",
        "senha": "Senha123!",
        "tipo": "produtor"
    })

    assert cadastro.status_code == 201

    # Fazer login
    login = cliente_api.post("/login", json={
        "email": "produtor_preco_negativo@teste.com",
        "senha": "Senha123!"
    })

    assert login.status_code == 200

    # Tentar cadastrar produto com preço negativo
    resposta = cliente_api.post(
        "/produtos",
        data={
            "nome": "Produto Teste",
            "preco": "-50.00",
            "quantidade": "100",
            "unidade": "kg",
            "categoria": "Grãos",
            "descricao": "Produto para teste",
            "status_produto": "disponivel"
        }
    )

    assert resposta.status_code >= 400
    