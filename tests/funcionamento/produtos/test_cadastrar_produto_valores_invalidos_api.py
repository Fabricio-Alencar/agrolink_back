# O que estamos testando?
# 1. A API rejeita preços que não sejam numéricos?
# 2. A API retorna HTTP 422 para valores inválidos?
# 3. O sistema impede o cadastro de produtos com dados incorretos?
# 4. Um produto com informações inválidas deixa de ser cadastrado?


def test_impedir_cadastro_produto_com_preco_invalido(cliente_api):
    # Cadastrar produtor
    cadastro = cliente_api.post("/cadastro", json={
        "nome": "Produtor Teste",
        "email": "produtor_valor_invalido@teste.com",
        "senha": "Senha123!",
        "tipo": "produtor"
    })

    assert cadastro.status_code == 201

    # Fazer login
    login = cliente_api.post("/login", json={
        "email": "produtor_valor_invalido@teste.com",
        "senha": "Senha123!"
    })

    assert login.status_code == 200

    # Tentar cadastrar produto com preço inválido
    resposta = cliente_api.post(
        "/produtos",
        data={
            "nome": "Produto Teste",
            "preco": "valor_invalido",
            "quantidade": "100",
            "unidade": "kg",
            "categoria": "Grãos",
            "descricao": "Produto para teste",
            "status_produto": "disponivel"
        }
    )

    assert resposta.status_code == 422