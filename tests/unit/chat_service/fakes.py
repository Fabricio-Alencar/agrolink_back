class MensagemFake:
    def __init__(self, **dados):
        for chave, valor in dados.items():
            setattr(self, chave, valor)


class ConversaFake:
    def __init__(self, **dados):
        for chave, valor in dados.items():
            setattr(self, chave, valor)


class NegociacaoFake:
    def __init__(self, **dados):
        for chave, valor in dados.items():
            setattr(self, chave, valor)


class UsuarioFake:
    def __init__(self, **dados):
        for chave, valor in dados.items():
            setattr(self, chave, valor)