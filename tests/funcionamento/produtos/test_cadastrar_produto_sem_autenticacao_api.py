# O que estamos testando?
# 1. Um usuário não autenticado consegue cadastrar um produto?
# 2. A API retorna HTTP 401 para uma requisição sem autenticação?
# 3. O sistema impede cadastros feitos por usuários sem sessão válida?
# 4. A API protege o cadastro de produtos contra acessos não autorizados?


def test_impedir_cadastro_sem_autenticacao(cliente_api):
    resposta = cliente_api.post(
        "/produtos",
        data={
            "nome": "Produto Teste",
            "preco": "50.00",
            "quantidade": "100",
            "unidade": "kg",
            "categoria": "Grãos",
            "descricao": "Produto para teste",
            "status_produto": "disponivel"
        }
    )

    assert resposta.status_code == 401