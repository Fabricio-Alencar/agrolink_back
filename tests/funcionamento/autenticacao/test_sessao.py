# o que o teste testa? : JWT válido, inválido, expirado e ausência de autenticação
# Envio do cookie, validação do JWT e recuperação do usuário

def test_consultar_sessao_autenticada(cliente_api):
    # Cadastra um usuário
    dados = {
        "nome": "Usuario Sessao",
        "email": "sessao_api@agrolink.com",
        "senha": "SenhaTeste123!",
        "tipo": "produtor"
    }

    cadastro = cliente_api.post("/cadastro", json=dados)
    assert cadastro.status_code == 201

    # Realiza o login
    login = cliente_api.post(
        "/login",
        json={
            "email": dados["email"],
            "senha": dados["senha"]
        }
    )

    assert login.status_code == 200
    assert "access_token" in cliente_api.cookies

    # Consulta a sessão autenticada
    resposta = cliente_api.get("/session")

    assert resposta.status_code == 200

    resultado = resposta.json()

    assert resultado["logado"] is True
    assert resultado["nome"] == dados["nome"]
    assert resultado["tipo"] == dados["tipo"]