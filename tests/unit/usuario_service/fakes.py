class UsuarioFake:
    """Representa um usuário falso para os testes."""

    def __init__(self, **dados):
        for chave, valor in dados.items():
            setattr(self, chave, valor)