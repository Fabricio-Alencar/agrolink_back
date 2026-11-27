"""
TESTES DE INTEGRAÇÃO - verificam se rotas, serviços, banco de dados e cache
funcionam juntos no fluxo completo da avaliação.
"""


# INT-01: avaliação registrada aparece no perfil público do produtor
def test_int01_avaliacao_aparece_no_perfil_publico(cenario):
    r = cenario["comprador"].post(
        f"/negociacoes/{cenario['negociacao_id']}/avaliar",
        json={"nota": 4.5, "comentario": "Produtos frescos e entrega no prazo"},
    )
    assert r.status_code == 200
    assert r.json()["media_produtor"] == 4.5

    perfil = cenario["comprador"].get(f"/produtores/{cenario['produtor_id']}").json()

    assert perfil["media_avaliacoes"] == 4.5
    assert perfil["total_avaliacoes"] == 1
    assert perfil["distribuicao"]["4.5"] == 1
    assert perfil["avaliacoes"][0]["comentario"] == "Produtos frescos e entrega no prazo"
    assert perfil["avaliacoes"][0]["avaliador_nome"] == "Mercado Bom"
    assert perfil["produtos"][0]["id"] == cenario["produto_id"]


# INT-02: a média nova chega ao marketplace (cache invalidado)
def test_int02_media_atualizada_no_marketplace(cenario, redis_falso):
    comprador = cenario["comprador"]

    # 1ª consulta: marketplace sem avaliações, resultado vai para o cache
    antes = comprador.get("/produtos").json()
    produto = next(p for p in antes if p["id"] == cenario["produto_id"])
    assert produto["produtor_avaliacao"] is None
    assert "marketplace" in redis_falso.dados

    comprador.post(f"/negociacoes/{cenario['negociacao_id']}/avaliar", json={"nota": 4})

    # A avaliação limpou o cache, então a nova consulta já traz a média
    assert "marketplace" in redis_falso.chaves_apagadas
    depois = comprador.get("/produtos").json()
    produto = next(p for p in depois if p["id"] == cenario["produto_id"])
    assert produto["produtor_avaliacao"] == 4.0
    assert produto["produtor_total_avaliacoes"] == 1


# INT-03: a lista de pedidos dos dois lados mostra a avaliação feita
def test_int03_avaliacao_aparece_na_lista_de_pedidos(cenario):
    cenario["comprador"].post(
        f"/negociacoes/{cenario['negociacao_id']}/avaliar",
        json={"nota": 5, "comentario": "Excelente"},
    )

    for cliente, tipo in ((cenario["comprador"], "estabelecimento"), (cenario["produtor"], "produtor")):
        pedidos = cliente.get(f"/negociacoes/{tipo}").json()
        pedido = next(p for p in pedidos if p["id"] == cenario["negociacao_id"])
        assert pedido["avaliacao"]["nota"] == 5
        assert pedido["avaliacao"]["comentario"] == "Excelente"
        assert pedido["produtor_avaliacao"] == 5.0


# INT-04: média de várias avaliações gravada também na tabela de usuários
def test_int04_media_de_varios_pedidos(cenario):
    from tests.avaliacoes.conftest import fazer_pedido, finalizar_pedido
    from database import SessionLocal
    from models import Usuario

    produtor, comprador = cenario["produtor"], cenario["comprador"]
    segundo = fazer_pedido(comprador, cenario["produto_id"])
    finalizar_pedido(produtor, comprador, segundo)

    comprador.post(f"/negociacoes/{cenario['negociacao_id']}/avaliar", json={"nota": 5})
    r = comprador.post(f"/negociacoes/{segundo}/avaliar", json={"nota": 3.5})

    assert r.json()["media_produtor"] == 4.2  # (5 + 3,5) / 2 = 4,25
    assert r.json()["total_avaliacoes"] == 2

    db = SessionLocal()
    try:
        assert db.get(Usuario, cenario["produtor_id"]).avaliacao == 4.2
    finally:
        db.close()
