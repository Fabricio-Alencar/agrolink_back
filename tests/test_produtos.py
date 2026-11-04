
import pytest

from models.usuario import Usuario
from models.produto import Produto
from services import produto_service


def criar_dois_produtores_com_produto(banco_teste):
    """
    Cria dois produtores e um produto pertencente ao produtor B.
    Retorna os IDs dos usuários e do produto.
    """

    db = banco_teste()

    try:
        produtor_a = Usuario(
            nome="Produtor A",
            email="produtor.a@teste.com",
            senha="hash_teste_a",
            tipo="produtor"
        )

        produtor_b = Usuario(
            nome="Produtor B",
            email="produtor.b@teste.com",
            senha="hash_teste_b",
            tipo="produtor"
        )

        db.add_all([produtor_a, produtor_b])
        db.commit()

        db.refresh(produtor_a)
        db.refresh(produtor_b)

        produto_b = Produto(
            nome="Produto do Produtor B",
            preco=10.0,
            quantidade=50.0,
            unidade="kg",
            categoria="Grãos",
            descricao="Produto utilizado no teste de IDOR",
            status="disponivel",
            produtor_id=produtor_b.id,
            foto="foto_generica.png"
        )

        db.add(produto_b)
        db.commit()
        db.refresh(produto_b)

        return produtor_a.id, produtor_b.id, produto_b.id

    finally:
        db.close()


class TestAutorizacaoProdutos:

    def test_produtor_nao_consegue_atualizar_produto_de_outro(
        self, banco_teste
    ):
        """
        Verifica se o produtor A é impedido de atualizar
        um produto pertencente ao produtor B.
        """

        produtor_a_id, produtor_b_id, produto_id = (
            criar_dois_produtores_com_produto(banco_teste)
        )

        dados_atualizacao = {
            "nome": "Produto alterado indevidamente",
            "preco": 999.0,
            "quantidade": 1.0,
            "unidade": "unidade",
            "categoria": "Teste",
            "descricao": "Tentativa de alteração não autorizada",
            "status": "indisponivel"
        }

        with pytest.raises(
            Exception,
            match="Você não tem permissão para editar este produto"
        ):
            produto_service.atualizar_produto(
                produto_id,
                produtor_a_id,
                dados_atualizacao,
                None
            )

        # Confirma que o produto de B continua intacto.
        db = banco_teste()

        try:
            produto = db.get(Produto, produto_id)

            assert produto is not None
            assert produto.produtor_id == produtor_b_id
            assert produto.nome == "Produto do Produtor B"
            assert produto.preco == 10.0
            assert produto.quantidade == 50.0

        finally:
            db.close()

    def test_produtor_nao_consegue_excluir_produto_de_outro(
        self, banco_teste
    ):
        """
        Verifica se o produtor A é impedido de excluir
        um produto pertencente ao produtor B.
        """

        produtor_a_id, produtor_b_id, produto_id = (
            criar_dois_produtores_com_produto(banco_teste)
        )

        with pytest.raises(
            Exception,
            match="Você não tem permissão para excluir este produto"
        ):
            produto_service.deletar_produto(
                produto_id,
                produtor_a_id
            )

        # Confirma que o produto de B continua cadastrado.
        db = banco_teste()

        try:
            produto = db.get(Produto, produto_id)

            assert produto is not None
            assert produto.produtor_id == produtor_b_id
            assert produto.nome == "Produto do Produtor B"

        finally:
            db.close()

    def test_produtor_nao_visualiza_produtos_de_outro(
        self, banco_teste
    ):
        """
        Verifica se a listagem retorna somente os produtos
        pertencentes ao produtor autenticado.
        """

        produtor_a_id, produtor_b_id, produto_b_id = (
            criar_dois_produtores_com_produto(banco_teste)
        )

        # Produtor A consulta seus próprios produtos.
        produtos_a = produto_service.listar_produtos_produtor(
            produtor_a_id
        )

        # O produto pertencente ao produtor B não deve aparecer.
        ids_produtos_a = [produto.id for produto in produtos_a]

        assert produto_b_id not in ids_produtos_a

        # Confirma que o produto continua pertencendo ao produtor B.
        db = banco_teste()

        try:
            produto_b = db.get(Produto, produto_b_id)

            assert produto_b is not None
            assert produto_b.produtor_id == produtor_b_id

        finally:
            db.close()
