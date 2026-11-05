# o que o teste testa? : 	Login válido, senha incorreta e usuário inexistente
#Validação das credenciais e emissão do JWT

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
