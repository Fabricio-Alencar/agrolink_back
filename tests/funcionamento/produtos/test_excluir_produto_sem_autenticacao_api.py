# O que estamos testando?
# 1. Um usuário não autenticado consegue excluir um produto?
# 2. A API retorna HTTP 401 para uma requisição sem autenticação?
# 3. O sistema impede exclusões feitas por usuários sem sessão válida?
# 4. Os produtos permanecem protegidos contra acessos não autorizados?


def test_impedir_exclusao_sem_autenticacao(cliente_api):
    resposta = cliente_api.delete("/produtos/1")

    assert resposta.status_code == 401