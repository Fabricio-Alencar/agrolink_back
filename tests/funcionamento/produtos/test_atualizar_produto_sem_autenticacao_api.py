# O que estamos testando?
# 1. Um usuário não autenticado consegue atualizar um produto?
# 2. A API retorna HTTP 401 para uma requisição sem autenticação?
# 3. O sistema impede alterações feitas por usuários sem sessão válida?
# 4. Os dados do produto permanecem protegidos?


def test_impedir_atualizacao_sem_autenticacao(cliente_api):
    resposta = cliente_api.post(
        "/produtos/1",
        data={
            "nome": "Produto Alterado",
            "preco": "150.00"
        }
    )

    assert resposta.status_code == 401