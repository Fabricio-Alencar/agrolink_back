from models.produto import Produto


# O que estamos testando?
# 1. Um produtor autenticado consegue listar seus produtos?
# 2. A API retorna HTTP 200?
# 3. A listagem apresenta somente produtos pertencentes ao produtor autenticado?
# 4. Os produtos de outros produtores permanecem ocultos?


def test_listar_somente_produtos_do_proprio_produtor(cliente_api, banco_teste):
    # Cadastrar o primeiro produtor
    cadastro1 = cliente_api.post("/cadastro", json={
        "nome": "Produtor Um",
        "email": "produtor_um@teste.com",
        "senha": "Senha123!",
        "tipo": "produtor"
    })

    assert cadastro1.status_code == 201

    # Cadastrar o segundo produtor
    cadastro2 = cliente_api.post("/cadastro", json={
        "nome": "Produtor Dois",
        "email": "produtor_dois@teste.com",
        "senha": "Senha123!",
        "tipo": "produtor"
    })

    assert cadastro2.status_code == 201

    id_produtor1 = cadastro1.json()["user"]["id"]
    id_produtor2 = cadastro2.json()["user"]["id"]

    # Criar produtos para os dois produtores
    db = banco_teste()

    produto1 = Produto(
        nome="Arroz",
        preco=50.00,
        quantidade=100,
        unidade="kg",
        categoria="Grãos",
        descricao="Arroz do produtor um",
        status="disponivel",
        foto="foto_generica.png",
        produtor_id=id_produtor1
    )

    produto2 = Produto(
        nome="Feijão",
        preco=8.50,
        quantidade=50,
        unidade="kg",
        categoria="Grãos",
        descricao="Feijão do produtor dois",
        status="disponivel",
        foto="foto_generica.png",
        produtor_id=id_produtor2
    )

    db.add_all([produto1, produto2])
    db.commit()
    db.close()

    # Autenticar o primeiro produtor
    login = cliente_api.post("/login", json={
        "email": "produtor_um@teste.com",
        "senha": "Senha123!"
    })

    assert login.status_code == 200

    # Listar produtos
    resposta = cliente_api.get("/meus-produtos")

    assert resposta.status_code == 200

    produtos = resposta.json()

    # Verificar se somente o produto do primeiro produtor aparece
    nomes_produtos = [produto["nome"] for produto in produtos]

    assert "Arroz" in nomes_produtos
    assert "Feijão" not in nomes_produtos