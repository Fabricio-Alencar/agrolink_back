# o que o teste testa? exclui o usuario e certifica de 
# que nn é mais valido as credenciais 

def test_excluir_conta_autenticado(cliente_api):
    # Cadastra um usuário
    dados = {
        "nome": "Usuario Exclusao",
        "email": "exclusao_api@agrolink.com",
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

    # Exclui a conta
    resposta = cliente_api.delete("/perfil")

    assert resposta.status_code == 200
    assert resposta.json()["msg"] == "Conta excluída com sucesso"

    # Verifica se a sessão não é mais válida
    sessao = cliente_api.get("/session")

    assert sessao.status_code == 401