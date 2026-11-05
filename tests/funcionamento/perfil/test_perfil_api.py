#o que o teste testa? : Consulta de perfil

def test_consultar_perfil_autenticado(cliente_api):
    # Cadastra um usuário
    dados = {
        "nome": "Usuario Perfil",
        "email": "perfil_api@agrolink.com",
        "senha": "SenhaTeste123!",
        "tipo": "produtor"
    }

    cadastro = cliente_api.post("/cadastro", json=dados)
    assert cadastro.status_code == 201

    # Realiza login
    login = cliente_api.post(
        "/login",
        json={
            "email": dados["email"],
            "senha": dados["senha"]
        }
    )
    assert login.status_code == 200

    # Consulta o perfil
    resposta = cliente_api.get("/perfil")

    assert resposta.status_code == 200

    resultado = resposta.json()

    assert resultado["nome"] == dados["nome"]
    assert resultado["email"] == dados["email"]