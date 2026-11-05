from models.produto import Produto
# O que estamos testando?
# 1. Um produtor autenticado consegue excluir seu produto?
# 2. A API retorna HTTP 200?
# 3. O produto é realmente removido do banco de dados?
# 4. A API retorna a mensagem de confirmação e o identificador do produto excluído?

def test_excluir_produto_pela_api(cliente_api, banco_teste):
    # Cadastrar produtor
    cadastro = cliente_api.post("/cadastro", json={
        "nome": "Produtor Teste",
        "email": "produtor_exclusao@teste.com",
        "senha": "Senha123!",
        "tipo": "produtor"
    })

    assert cadastro.status_code == 201

    # Fazer login
    login = cliente_api.post("/login", json={
        "email": "produtor_exclusao@teste.com",
        "senha": "Senha123!"
    })

    assert login.status_code == 200

    # Criar produto diretamente no banco de teste
    db = banco_teste()

    produto = Produto(
        nome="Arroz",
        preco=50.00,
        quantidade=100,
        unidade="kg",
        categoria="Grãos",
        descricao="Arroz para teste",
        status="disponivel",
        foto="foto_generica.png",
        produtor_id=cadastro.json()["user"]["id"]
    )

    db.add(produto)
    db.commit()
    db.refresh(produto)

    produto_id = produto.id
    db.close()

    # Excluir produto pela API
    resposta = cliente_api.delete(f"/produtos/{produto_id}")

    assert resposta.status_code == 200
    assert resposta.json()["id_excluido"] == produto_id
    assert resposta.json()["msg"] == "Produto removido com sucesso"

    # Verificar se o produto foi realmente removido do banco
    db = banco_teste()
    produto_excluido = db.get(Produto, produto_id)

    assert produto_excluido is None

    db.close()