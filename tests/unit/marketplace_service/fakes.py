
class ProdutoFake:
    def __init__(self, **dados):
        for chave, valor in dados.items():
            setattr(self, chave, valor)


class ProdutorFake:
    def __init__(self, **dados):
        for chave, valor in dados.items():
            setattr(self, chave, valor)


class NegociacaoFake:
    def __init__(self, **dados):
        for chave, valor in dados.items():
            setattr(self, chave, valor)
