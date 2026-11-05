# O que estamos testando?
# 1. Um usuário não autenticado consegue acessar a listagem de seus produtos?
# 2. A API retorna HTTP 401 para uma requisição sem autenticação?
# 3. O sistema impede o acesso a informações protegidas?
# 4. A API não disponibiliza dados de produtos sem uma sessão válida?


def test_impedir_listagem_sem_autenticacao(cliente_api):
    resposta = cliente_api.get("/meus-produtos")

    assert resposta.status_code == 401