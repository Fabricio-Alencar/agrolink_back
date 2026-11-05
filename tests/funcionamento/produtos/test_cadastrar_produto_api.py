from models.produto import Produto


# O que estamos testando?
# 1. Um produtor consegue cadastrar um produto pela API?
# 2. Os dados enviados são persistidos no banco?
# 3. A API retorna o código HTTP 201 Created?
# 4. O produto criado possui um identificador e os dados esperados?

def test_cadastrar_produto_pela_api(cliente_api, banco_teste):

    # Cadastra um produtor
    dados_usuario = {
        "nome": "Produtor Teste",
        "email": "produtor_produto@agrolink.com",
        "senha": "SenhaTeste123!",
        "tipo": "produtor"
    }

    cadastro = cliente_api.post(
        "/cadastro",
        json=dados_usuario
    )

    assert cadastro.status_code == 201

    # Realiza login
    login = cliente_api.post(
        "/login",
        json={
            "email": dados_usuario["email"],
            "senha": dados_usuario["senha"]
        }
    )

    assert login.status_code == 200

    # Cadastra um produto
    dados_produto = {
        "nome": "Milho",
        "preco": "80.50",
        "quantidade": "100",
        "unidade": "kg",
        "categoria": "Grãos",
        "descricao": "Milho de boa qualidade",
        "status_produto": "disponivel"
    }

    resposta = cliente_api.post(
        "/produtos",
        data=dados_produto
    )

    assert resposta.status_code == 201

    resultado = resposta.json()

    assert resultado["msg"] == "Produto criado com sucesso"
    assert resultado["produto"]["nome"] == dados_produto["nome"]
    assert resultado["produto"]["preco"] == 80.50
    assert "id" in resultado["produto"]

    # Verifica diretamente se o produto foi persistido no banco
    db = banco_teste()

    try:
        produto_salvo = db.get(
            Produto,
            resultado["produto"]["id"]
        )

        assert produto_salvo is not None
        assert produto_salvo.nome == dados_produto["nome"]
        assert produto_salvo.preco == 80.50
        assert produto_salvo.quantidade == 100
        assert produto_salvo.produtor_id == cadastro.json()["user"]["id"]

    finally:
        db.close()