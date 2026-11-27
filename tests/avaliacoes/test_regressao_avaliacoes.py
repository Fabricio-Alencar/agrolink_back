"""
TESTES DE REGRESSÃO - garantem que problemas já corrigidos durante o
desenvolvimento das avaliações não voltem a acontecer.
"""
from tests.avaliacoes.conftest import cadastrar_e_logar, criar_produto


# REG-01: produtor novo não pode começar com nota 5,0
# (antes o cadastro gravava 5.0 automaticamente na coluna avaliacao)
def test_reg01_produtor_novo_sem_nota_automatica(app):
    from database import SessionLocal
    from models import Usuario

    produtor, produtor_id = cadastrar_e_logar(app, "Produtor Novo", "novo@teste.com", "produtor")
    criar_produto(produtor)

    db = SessionLocal()
    try:
        assert db.get(Usuario, produtor_id).avaliacao is None
    finally:
        db.close()

    produto = produtor.get("/produtos").json()[0]
    assert produto["produtor_avaliacao"] is None
    assert produto["produtor_total_avaliacoes"] == 0


# REG-02: a média ignora o valor antigo da coluna usuarios.avaliacao
def test_reg02_media_ignora_valor_antigo_da_coluna(cenario):
    from database import SessionLocal
    from models import Usuario

    db = SessionLocal()
    try:
        db.get(Usuario, cenario["produtor_id"]).avaliacao = 5.0  # dado legado
        db.commit()
    finally:
        db.close()

    perfil = cenario["comprador"].get(f"/produtores/{cenario['produtor_id']}").json()
    assert perfil["media_avaliacoes"] is None

    cenario["comprador"].post(f"/negociacoes/{cenario['negociacao_id']}/avaliar", json={"nota": 2})
    perfil = cenario["comprador"].get(f"/produtores/{cenario['produtor_id']}").json()
    assert perfil["media_avaliacoes"] == 2.0


# REG-03: avaliar atualiza a data do pedido (pedido sobe na lista do produtor)
def test_reg03_avaliacao_atualiza_data_do_pedido(cenario):
    from database import SessionLocal
    from models import Negociacao

    db = SessionLocal()
    try:
        antes = db.get(Negociacao, cenario["negociacao_id"]).data_atualizacao
    finally:
        db.close()

    cenario["comprador"].post(f"/negociacoes/{cenario['negociacao_id']}/avaliar", json={"nota": 4})

    db = SessionLocal()
    try:
        depois = db.get(Negociacao, cenario["negociacao_id"]).data_atualizacao
    finally:
        db.close()
    assert depois > antes


# REG-04: confirmar o recebimento finaliza o pedido mesmo sem a
# confirmação de entrega do produtor (libera a avaliação na hora)
def test_reg04_recebimento_finaliza_pedido(app):
    from tests.avaliacoes.conftest import fazer_pedido

    produtor, _ = cadastrar_e_logar(app, "Produtor", "p2@teste.com", "produtor")
    comprador, _ = cadastrar_e_logar(app, "Mercado", "m2@teste.com", "estabelecimento")
    negociacao_id = fazer_pedido(comprador, criar_produto(produtor))
    produtor.put(f"/negociacoes/{negociacao_id}/status", json={"status": "aceito"})

    r = comprador.put(f"/negociacoes/{negociacao_id}/confirmar", json={"acao": "confirmar_recebimento"})

    assert r.json()["status_atual"] == "Finalizado"
    avaliar = comprador.post(f"/negociacoes/{negociacao_id}/avaliar", json={"nota": 5})
    assert avaliar.status_code == 200
