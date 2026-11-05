# O que estamos testando?
# 1. A API identifica quando um produto não existe?
# 2. A API retorna HTTP 400 ao tentar atualizar um produto inexistente?
# 3. O sistema impede alterações em registros que não existem?
# 4. A API retorna uma resposta de erro sem interromper seu funcionamento?


def test_impedir_atualizacao_produto_inexistente(cliente_api):
    # Cadastrar produtor
    cadastro = cliente_api.post("/cadastro", json={
        "nome": "Produtor Teste",
        "email": "produtor_inexistente@teste.com",
        "senha": "Senha123!",
        "tipo": "produtor"
    })

    assert cadastro.status_code == 201

    # Fazer login
    login = cliente_api.post("/login", json={
        "email": "produtor_inexistente@teste.com",
        "senha": "Senha123!"
    })

    assert login.status_code == 200

    # Tentar atualizar um produto inexistente
    resposta = cliente_api.post(
        "/produtos/999999",
        data={
            "nome": "Produto Alterado",
            "preco": "100.00"
        }
    )

    assert resposta.status_code == 400