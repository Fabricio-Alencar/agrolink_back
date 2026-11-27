"""
TESTES FUNCIONAIS - verificam pela API se as regras de negócio das
avaliações funcionam conforme o especificado.
"""
from tests.avaliacoes.conftest import fazer_pedido


# FUN-01: só pedidos finalizados podem ser avaliados
def test_fun01_pedido_nao_finalizado_nao_pode_ser_avaliado(cenario):
    pendente = fazer_pedido(cenario["comprador"], cenario["produto_id"])

    r = cenario["comprador"].post(f"/negociacoes/{pendente}/avaliar", json={"nota": 5})

    assert r.status_code == 400
    assert "finalizada" in r.json()["detail"]["erro"]


# FUN-02: a avaliação é definitiva (não pode avaliar duas vezes)
def test_fun02_avaliacao_e_definitiva(cenario):
    url = f"/negociacoes/{cenario['negociacao_id']}/avaliar"

    primeira = cenario["comprador"].post(url, json={"nota": 5})
    segunda = cenario["comprador"].post(url, json={"nota": 1})

    assert primeira.status_code == 200
    assert segunda.status_code == 409
    perfil = cenario["comprador"].get(f"/produtores/{cenario['produtor_id']}").json()
    assert perfil["media_avaliacoes"] == 5.0  # a nota original não mudou


# FUN-03: comentário é opcional
def test_fun03_comentario_opcional(cenario):
    r = cenario["comprador"].post(
        f"/negociacoes/{cenario['negociacao_id']}/avaliar", json={"nota": 3, "comentario": "   "}
    )

    assert r.status_code == 200
    perfil = cenario["comprador"].get(f"/produtores/{cenario['produtor_id']}").json()
    assert perfil["avaliacoes"][0]["comentario"] is None


# FUN-04: comentário tem limite de 500 caracteres
def test_fun04_comentario_maior_que_500_caracteres(cenario):
    url = f"/negociacoes/{cenario['negociacao_id']}/avaliar"

    longo = cenario["comprador"].post(url, json={"nota": 4, "comentario": "a" * 501})
    limite = cenario["comprador"].post(url, json={"nota": 4, "comentario": "a" * 500})

    assert longo.status_code == 400
    assert limite.status_code == 200


# FUN-05: pedido inexistente
def test_fun05_pedido_inexistente(cenario):
    r = cenario["comprador"].post("/negociacoes/9999/avaliar", json={"nota": 5})

    assert r.status_code == 404


# FUN-06: produtor sem avaliações aparece como "Sem avaliações"
def test_fun06_produtor_sem_avaliacoes(cenario):
    perfil = cenario["comprador"].get(f"/produtores/{cenario['produtor_id']}").json()

    assert perfil["media_avaliacoes"] is None
    assert perfil["total_avaliacoes"] == 0
    assert perfil["avaliacoes"] == []


# FUN-07: duas avaliações enviadas ao mesmo tempo para o mesmo pedido
# (ex.: duas abas abertas). Só uma pode ser gravada e a outra deve receber 409.
def test_fun07_avaliacoes_simultaneas(cenario):
    import threading
    from tests.avaliacoes.conftest import novo_cliente

    url = f"/negociacoes/{cenario['negociacao_id']}/avaliar"
    respostas = []

    def enviar(nota):
        cliente = novo_cliente(cenario["app"])
        cliente.cookies = cenario["comprador"].cookies
        try:
            respostas.append(cliente.post(url, json={"nota": nota}).status_code)
        except Exception as erro:  # erro interno do servidor
            respostas.append(type(erro).__name__)

    threads = [threading.Thread(target=enviar, args=(nota,)) for nota in (5, 1, 3, 4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert sorted(respostas, key=str) == [200, 409, 409, 409]
    perfil = cenario["comprador"].get(f"/produtores/{cenario['produtor_id']}").json()
    assert perfil["total_avaliacoes"] == 1
