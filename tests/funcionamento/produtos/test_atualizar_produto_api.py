from models.produto import Produto


# O que estamos testando?
# 1. Um produtor autenticado consegue atualizar seu produto?
# 2. A API retorna HTTP 200?
# 3. Os dados atualizados são persistidos no banco?
# 4. O produto mantém seu identificador original?

def test_atualizar_produto_pela_api(cliente_api, banco_teste):

    # Cadastra um produtor
    dados_usuario = {
        "nome": "Produtor Atualizacao",
        "email": "produtor_atualizacao@agrolink.com",
        "senha": "SenhaTeste123!",
        "tipo": "produtor"
    }

    cadastro = cliente_api.post("/cadastro", json=dados_usuario)
    assert cadastro.status_code == 201

    produtor_id = cadastro.json()["user"]["id"]

    # Realiza login
    login = cliente_api.post(
        "/login",
        json={
            "email": dados_usuario["email"],
            "senha": dados_usuario["senha"]
        }
    )
    assert login.status_code == 200

    # Insere um produto no banco de testes
    db = banco_teste()

    try:
        produto = Produto(
            nome="Milho",
            preco=80.50,
            quantidade=100,
            unidade="kg",
            categoria="Grãos",
            descricao="Milho comum",
            status="disponivel",
            foto="foto_generica.png",
            produtor_id=produtor_id
        )

        db.add(produto)
        db.commit()
        db.refresh(produto)

        produto_id = produto.id

    finally:
        db.close()

    # Atualiza o produto pela API
    resposta = cliente_api.post(
        f"/produtos/{produto_id}",
        data={
            "nome": "Milho Premium",
            "preco": "100.00"
        }
    )

    assert resposta.status_code == 200

    resultado = resposta.json()

    assert resultado["msg"] == "Produto atualizado com sucesso"
    assert resultado["produto"]["id"] == produto_id
    assert resultado["produto"]["nome"] == "Milho Premium"

    # Verifica diretamente se as alterações foram persistidas
    db = banco_teste()

    try:
        produto_atualizado = db.get(Produto, produto_id)

        assert produto_atualizado is not None
        assert produto_atualizado.nome == "Milho Premium"
        assert produto_atualizado.preco == 100.00

        # Verifica se os campos não enviados foram preservados
        assert produto_atualizado.quantidade == 100
        assert produto_atualizado.descricao == "Milho comum"

    finally:
        db.close()