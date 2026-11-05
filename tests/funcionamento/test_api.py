
#o que o teste testa: 	Disponibilidade da rota principal /

def test_api_esta_funcionando(cliente_api):
    resposta = cliente_api.get("/")

    assert resposta.status_code == 200
    assert resposta.json() == {
        "message": "AgroLink API funcionando!"
    }