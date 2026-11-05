# O que estamos testando?
# 1. A API rejeita quantidades que não sejam numéricas?
# 2. A API retorna HTTP 422 para uma quantidade inválida?
# 3. O sistema impede o cadastro de produtos com quantidades incorretas?
# 4. Um produto com quantidade inválida deixa de ser cadastrado?


def test_impedir_cadastro_produto_com_quantidade_invalida(cliente_api):
    # Cadastrar produtor
    cadastro = cliente_api.post("/cadastro", json={
        "nome": "Produtor Teste",
        "email": "produtor_quantidade_invalida@teste.com",
        "senha": "Senha123!",
        "tipo": "produtor"
    })

    assert cadastro.status_code == 201

    # Fazer login
    login = cliente_api.post("/login", json={
        "email": "produtor_quantidade_invalida@teste.com",
        "senha": "Senha123!"
    })

    assert login.status_code == 200

    # Tentar cadastrar produto com quantidade inválida
    resposta = cliente_api.post(
        "/produtos",
        data={
            "nome": "Produto Teste",
            "preco": "50.00",
            "quantidade": "quantidade_invalida",
            "unidade": "kg",
            "categoria": "Grãos",
            "descricao": "Produto para teste",
            "status_produto": "disponivel"
        }
    )

    assert resposta.status_code == 422