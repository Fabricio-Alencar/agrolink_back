"""
TESTES DE SEGURANÇA - tentativas de acesso indevido às avaliações.
"""
from tests.avaliacoes.conftest import cadastrar_e_logar, novo_cliente


# SEG-01: sem login não é possível avaliar nem ver o perfil público
def test_seg01_sem_autenticacao(cenario):
    anonimo = novo_cliente(cenario["app"])

    avaliar = anonimo.post(f"/negociacoes/{cenario['negociacao_id']}/avaliar", json={"nota": 5})
    perfil = anonimo.get(f"/produtores/{cenario['produtor_id']}")

    assert avaliar.status_code == 401
    assert perfil.status_code == 401


# SEG-02: token adulterado é recusado
def test_seg02_token_adulterado(cenario):
    import jwt

    falso = jwt.encode({"sub": str(cenario["comprador_id"]), "tipo": "estabelecimento"},
                       "chave-errada", algorithm="HS256")
    cliente = novo_cliente(cenario["app"])
    cliente.cookies.set("access_token", falso)

    r = cliente.post(f"/negociacoes/{cenario['negociacao_id']}/avaliar", json={"nota": 5})

    assert r.status_code == 401


# SEG-03: o produtor não pode avaliar a si mesmo
def test_seg03_produtor_nao_avalia_a_si_mesmo(cenario):
    r = cenario["produtor"].post(f"/negociacoes/{cenario['negociacao_id']}/avaliar", json={"nota": 5})

    assert r.status_code == 403


# SEG-04: um estabelecimento que não participou do pedido não pode avaliar
def test_seg04_estabelecimento_de_fora_nao_avalia(cenario):
    intruso, _ = cadastrar_e_logar(cenario["app"], "Outro Mercado", "outro@teste.com", "estabelecimento")

    r = intruso.post(f"/negociacoes/{cenario['negociacao_id']}/avaliar", json={"nota": 0.5})

    assert r.status_code == 403
    perfil = intruso.get(f"/produtores/{cenario['produtor_id']}").json()
    assert perfil["total_avaliacoes"] == 0


# SEG-05: o perfil público não expõe e-mail nem telefone do produtor
def test_seg05_perfil_publico_nao_expoe_dados_pessoais(cenario):
    perfil = cenario["comprador"].get(f"/produtores/{cenario['produtor_id']}").json()

    assert "email" not in perfil
    assert "telefone" not in perfil
    assert "senha" not in perfil


# SEG-06: o perfil público só existe para produtores
def test_seg06_perfil_publico_de_estabelecimento(cenario):
    r = cenario["produtor"].get(f"/produtores/{cenario['comprador_id']}")

    assert r.status_code == 404


# SEG-07: comentário com HTML/script é guardado como texto, sem executar
def test_seg07_comentario_com_script(cenario):
    script = "<script>alert('x')</script>"
    r = cenario["comprador"].post(
        f"/negociacoes/{cenario['negociacao_id']}/avaliar", json={"nota": 4, "comentario": script}
    )

    assert r.status_code == 200
    perfil = cenario["comprador"].get(f"/produtores/{cenario['produtor_id']}").json()
    assert perfil["avaliacoes"][0]["comentario"] == script
