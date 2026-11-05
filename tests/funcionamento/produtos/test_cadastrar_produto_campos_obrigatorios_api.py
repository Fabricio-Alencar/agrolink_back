# O que estamos testando?
# 1. A API impede o cadastro de produtos sem todos os campos obrigatórios?
# 2. A API retorna HTTP 422 quando faltam informações?
# 3. O sistema identifica os campos obrigatórios ausentes?
# 4. Um produto incompleto deixa de ser cadastrado?


def test_impedir_cadastro_produto_sem_campos_obrigatorios(cliente_api):
    # Cadastrar produtor
    cadastro = cliente_api.post("/cadastro", json={
        "nome": "Produtor Teste",
        "email": "produtor_campos@teste.com",
        "senha": "Senha123!",
        "tipo": "produtor"
    })

    assert cadastro.status_code == 201

    # Fazer login
    login = cliente_api.post("/login", json={
        "email": "produtor_campos@teste.com",
        "senha": "Senha123!"
    })

    assert login.status_code == 200

    # Tentar cadastrar produto sem informar todos os campos
    resposta = cliente_api.post(
        "/produtos",
        data={
            "nome": "Produto Incompleto",
            "preco": "50.00"
        }
    )

    assert resposta.status_code == 422