from models.produto import Produto


# O que estamos testando?
# 1. A API rejeita valores inválidos durante a atualização de um produto?
# 2. A API retorna um código HTTP de erro?
# 3. Os dados originais do produto permanecem preservados?
# 4. O sistema impede que informações inválidas sejam persistidas no banco?


def test_impedir_atualizacao_produto_com_preco_invalido(cliente_api, banco_teste):
    # Cadastrar produtor
    cadastro = cliente_api.post("/cadastro", json={
        "nome": "Produtor Teste",
        "email": "produtor_preco_invalido@teste.com",
        "senha": "Senha123!",
        "tipo": "produtor"
    })

    assert cadastro.status_code == 201

    # Fazer login
    login = cliente_api.post("/login", json={
        "email": "produtor_preco_invalido@teste.com",
        "senha": "Senha123!"
    })

    assert login.status_code == 200

    # Criar produto
    db = banco_teste()

    produto = Produto(
        nome="Soja",
        preco=120.00,
        quantidade=100,
        unidade="kg",
        categoria="Grãos",
        descricao="Soja para teste",
        status="disponivel",
        foto="foto_generica.png",
        produtor_id=cadastro.json()["user"]["id"]
    )

    db.add(produto)
    db.commit()
    db.refresh(produto)

    produto_id = produto.id
    db.close()

    # Tentar atualizar com preço inválido
    resposta = cliente_api.post(
        f"/produtos/{produto_id}",
        data={
            "preco": "preco_invalido"
        }
    )

    assert resposta.status_code >= 400

    # Verificar se o preço original foi preservado
    db = banco_teste()
    produto_atualizado = db.get(Produto, produto_id)

    assert produto_atualizado is not None
    assert float(produto_atualizado.preco) == 120.00

    db.close()