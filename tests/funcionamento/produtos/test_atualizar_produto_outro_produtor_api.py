from models.produto import Produto


# O que estamos testando?
# 1. Um produtor consegue tentar atualizar o produto de outro produtor?
# 2. A API retorna HTTP 400 ao negar a operação?
# 3. Os dados originais do produto permanecem inalterados?
# 4. O sistema impede alterações em produtos pertencentes a outros usuários?


def test_impedir_atualizacao_produto_de_outro_produtor(cliente_api, banco_teste):
    # Cadastrar o proprietário do produto
    cadastro1 = cliente_api.post("/cadastro", json={
        "nome": "Produtor Proprietario",
        "email": "proprietario_update@teste.com",
        "senha": "Senha123!",
        "tipo": "produtor"
    })

    assert cadastro1.status_code == 201

    # Cadastrar outro produtor
    cadastro2 = cliente_api.post("/cadastro", json={
        "nome": "Outro Produtor",
        "email": "outro_update@teste.com",
        "senha": "Senha123!",
        "tipo": "produtor"
    })

    assert cadastro2.status_code == 201

    # Criar produto pertencente ao primeiro produtor
    db = banco_teste()

    produto = Produto(
        nome="Milho",
        preco=80.00,
        quantidade=100,
        unidade="kg",
        categoria="Grãos",
        descricao="Milho para teste",
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
        "email": "outro_update@teste.com",
        "senha": "Senha123!"
    })

    assert login.status_code == 200

    # Tentar atualizar o produto do primeiro produtor
    resposta = cliente_api.post(
        f"/produtos/{produto_id}",
        data={
            "nome": "Milho Alterado",
            "preco": "150.00"
        }
    )

    assert resposta.status_code == 400

    # Verificar se os dados originais foram preservados
    db = banco_teste()
    produto_existente = db.get(Produto, produto_id)

    assert produto_existente is not None
    assert produto_existente.nome == "Milho"
    assert float(produto_existente.preco) == 80.00
    assert produto_existente.quantidade == 100
    assert produto_existente.produtor_id == cadastro1.json()["user"]["id"]

    db.close()