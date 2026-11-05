from models.produto import Produto


# O que estamos testando?
# 1. Um produtor autenticado consegue tentar excluir o produto de outro produtor?
# 2. A API retorna HTTP 403 ao negar a operação?
# 3. O produto permanece cadastrado no banco?
# 4. O sistema impede a exclusão de produtos pertencentes a outros usuários?


def test_impedir_exclusao_produto_de_outro_produtor(cliente_api, banco_teste):
    # Cadastrar o proprietário do produto
    cadastro1 = cliente_api.post("/cadastro", json={
        "nome": "Produtor Proprietario",
        "email": "proprietario@teste.com",
        "senha": "Senha123!",
        "tipo": "produtor"
    })

    assert cadastro1.status_code == 201

    # Cadastrar outro produtor
    cadastro2 = cliente_api.post("/cadastro", json={
        "nome": "Outro Produtor",
        "email": "outroprodutor@teste.com",
        "senha": "Senha123!",
        "tipo": "produtor"
    })

    assert cadastro2.status_code == 201

    # Criar produto pertencente ao primeiro produtor
    db = banco_teste()

    produto = Produto(
        nome="Feijão",
        preco=8.50,
        quantidade=50,
        unidade="kg",
        categoria="Grãos",
        descricao="Feijão para teste",
        status="disponivel",
        foto="foto_generica.png",
        produtor_id=cadastro1.json()["user"]["id"]
    )

    db.add(produto)
    db.commit()
    db.refresh(produto)

    produto_id = produto.id
    db.close()

    # Autenticar o segundo produtor
    login = cliente_api.post("/login", json={
        "email": "outroprodutor@teste.com",
        "senha": "Senha123!"
    })

    assert login.status_code == 200

    # Tentar excluir o produto do primeiro produtor
    resposta = cliente_api.delete(f"/produtos/{produto_id}")

    assert resposta.status_code == 403

    # Verificar se o produto continua no banco
    db = banco_teste()
    produto_existente = db.get(Produto, produto_id)

    assert produto_existente is not None
    assert produto_existente.nome == "Feijão"
    assert produto_existente.produtor_id == cadastro1.json()["user"]["id"]

    db.close()