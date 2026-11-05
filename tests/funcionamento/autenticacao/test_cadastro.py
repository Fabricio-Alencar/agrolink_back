# o que o teste testa: Cadastro válido, duplicado e dados inválidos
#Endpoint, persistência e resposta HTTP 201
def test_cadastro_pela_api(cliente_api):
    dados = {
        "nome": "Usuario Teste",
        "email": "teste_api@agrolink.com",
        "senha": "SenhaTeste123!",
        "tipo": "produtor"
    }

    resposta = cliente_api.post("/cadastro", json=dados)

    assert resposta.status_code == 201

    resultado = resposta.json()

    assert resultado["user"]["nome"] == dados["nome"]
    assert resultado["user"]["tipo"] == dados["tipo"]
    assert "id" in resultado["user"]
