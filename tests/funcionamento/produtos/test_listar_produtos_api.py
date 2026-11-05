from models.produto import Produto


# O que estamos testando?
# 1. Um produtor autenticado consegue listar seus produtos?
# 2. A API retorna HTTP 200?
# 3. Os produtos retornados pertencem ao produtor autenticado?
# 4. Os dados dos produtos são apresentados corretamente?

def test_listar_produtos_do_produtor(cliente_api, banco_teste):

    # Cadastra um produtor
    dados_usuario = {
        "nome": "Produtor Listagem",
        "email": "produtor_listagem@agrolink.com",
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

    # Cadastra um produto diretamente no banco de teste
    db = banco_teste()

    try:
        produto = Produto(
            nome="Soja",
            preco=150.00,
            quantidade=200,
            unidade="kg",
            categoria="Grãos",
            descricao="Soja para comercialização",
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

    # Consulta os produtos pela API
    resposta = cliente_api.get("/meus-produtos")

    assert resposta.status_code == 200

    resultado = resposta.json()

    # Verifica se o produto cadastrado aparece na listagem
    assert len(resultado) == 1
    assert resultado[0]["id"] == produto_id
    assert resultado[0]["nome"] == "Soja"
    assert resultado[0]["preco"] == 150.00
    assert resultado[0]["quantidade"] == 200