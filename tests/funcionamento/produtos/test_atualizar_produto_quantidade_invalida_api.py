from uuid import uuid4

from models.produto import Produto


# O que estamos testando?
# 1. Se a API rejeita uma quantidade que não seja numérica.
# 2. Se o produto mantém a quantidade original após uma atualização inválida.
# 3. Se a tentativa de atualização não altera os dados já cadastrados.


def test_impedir_atualizacao_produto_com_quantidade_invalida(
    cliente_api, banco_teste
):
    email = f"produtor_{uuid4().hex[:8]}@teste.com"
    senha = "Senha123"

    # Criar usuário produtor
    cadastro = cliente_api.post(
        "/cadastro",
        json={
            "nome": "Produtor Teste",
            "email": email,
            "senha": senha,
            "tipo": "produtor"
        }
    )

    assert cadastro.status_code == 201

    produtor_id = cadastro.json()["user"]["id"]

    # Realizar login
    login = cliente_api.post(
        "/login",
        json={
            "email": email,
            "senha": senha
        }
    )

    assert login.status_code == 200

    # Criar produto diretamente no banco de teste
    db = banco_teste()

    produto = Produto(
        nome="Milho",
        preco=120.00,
        quantidade=10,
        unidade="kg",
        categoria="Grãos",
        descricao="Milho para teste",
        status="disponivel",
        foto="foto_generica.png",
        produtor_id=produtor_id
    )

    db.add(produto)
    db.commit()
    db.refresh(produto)

    produto_id = produto.id
    db.close()

    # Tentar atualizar o produto com uma quantidade inválida
    resposta = cliente_api.post(
        f"/produtos/{produto_id}",
        data={
            "quantidade": "quantidade_invalida"
        }
    )

    # A API deve rejeitar a quantidade inválida
    assert resposta.status_code == 422

    # Verificar se a quantidade original foi preservada
    db = banco_teste()
    produto_atualizado = db.get(Produto, produto_id)

    assert produto_atualizado is not None
    assert produto_atualizado.quantidade == 10

    db.close()