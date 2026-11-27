"""
TESTES UNITÁRIOS - funções do serviço de avaliações testadas isoladamente.
"""
import pytest

from tests.avaliacoes.conftest import cadastrar_e_logar


# UNI-01: validação da nota (escala de 0,5 a 5, de meia em meia estrela)
@pytest.mark.parametrize("nota", [0, 0.3, 5.5, -1, 4.25, "5", None, True])
def test_uni01_nota_invalida_e_recusada(cenario, nota):
    from services.avaliacoes_service import avaliar_produtor

    resultado, codigo = avaliar_produtor(cenario["negociacao_id"], cenario["comprador_id"], nota)

    assert codigo == 400
    assert "nota" in resultado["erro"].lower()


@pytest.mark.parametrize("nota", [0.5, 1, 2.5, 4.5, 5])
def test_uni01_nota_valida_e_aceita(app, nota):
    from tests.avaliacoes.conftest import criar_produto, fazer_pedido, finalizar_pedido
    from services.avaliacoes_service import avaliar_produtor

    produtor, _ = cadastrar_e_logar(app, "Produtor", "p@teste.com", "produtor")
    comprador, comprador_id = cadastrar_e_logar(app, "Mercado", "m@teste.com", "estabelecimento")
    negociacao_id = fazer_pedido(comprador, criar_produto(produtor))
    finalizar_pedido(produtor, comprador, negociacao_id)

    resultado, codigo = avaliar_produtor(negociacao_id, comprador_id, nota)

    assert codigo == 200
    assert resultado["nota"] == float(nota)


# UNI-02: cálculo da média e da quantidade de avaliações
def test_uni02_resumo_calcula_media_e_total(banco):
    from database import SessionLocal
    from models import Usuario, Avaliacao
    from services.avaliacoes_service import resumo_avaliacoes

    db = SessionLocal()
    try:
        produtor = Usuario(nome="P", email="p@t.com", senha="x", tipo="produtor")
        comprador = Usuario(nome="C", email="c@t.com", senha="x", tipo="estabelecimento")
        db.add_all([produtor, comprador])
        db.flush()
        for nota in (5, 4, 3.5):
            db.add(Avaliacao(avaliador_id=comprador.id, avaliado_id=produtor.id, nota=nota))
        db.commit()

        resumo = resumo_avaliacoes(db, [produtor.id, comprador.id])

        assert resumo[produtor.id] == {"media": 4.2, "total": 3}
        # Quem não tem avaliações não aparece (= "Sem avaliações")
        assert comprador.id not in resumo
    finally:
        db.close()


# UNI-03: conversão da avaliação para JSON
def test_uni03_avaliacao_para_json():
    from datetime import datetime
    from models import Avaliacao
    from services.avaliacoes_service import avaliacao_para_json

    avaliacao = Avaliacao(nota=4.5, comentario="Ótimo", data_criacao=datetime(2026, 11, 20, 10, 0))

    assert avaliacao_para_json(avaliacao) == {
        "nota": 4.5, "comentario": "Ótimo", "data": "2026-11-20T10:00:00"
    }
    assert avaliacao_para_json(None) is None
