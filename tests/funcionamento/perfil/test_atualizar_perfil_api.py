# o que o teste testa? : atualizar perfil

def test_atualizar_perfil_autenticado(cliente_api):
    # Cadastra um usuário
    dados = {
        "nome": "Usuario Perfil",
        "email": "atualizar_perfil@agrolink.com",
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

    # Atualiza o perfil
    resposta = cliente_api.post(
        "/perfil",
        data={
            "nome": "Usuario Atualizado"
        }
    )

    assert resposta.status_code == 200

    # Consulta o perfil atualizado
    perfil = cliente_api.get("/perfil")

    assert perfil.status_code == 200
    assert perfil.json()["nome"] == "Usuario Atualizado"