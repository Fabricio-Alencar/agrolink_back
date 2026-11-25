class FakeDB:
    def __init__(self, usuario=None, commit_error=None, delete_error=None):
        self.usuario = usuario
        self.commit_error = commit_error
        self.delete_error = delete_error

        self.committed = False
        self.rolled_back = False
        self.closed = False
        self.deleted = None
        self.refreshed = None

    def get(self, model, user_id):
        return self.usuario

    def commit(self):
        if self.commit_error:
            raise self.commit_error

        self.committed = True

    def refresh(self, usuario):
        self.refreshed = usuario

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True

    def delete(self, usuario):
        if self.delete_error:
            raise self.delete_error

        self.deleted = usuario


class FakeRedis:
    def __init__(self):
        self.deleted_keys = []

    def delete(self, key):
        self.deleted_keys.append(key)


class FakeUsuario:
    def __init__(self):
        self.id = 1
        self.nome = "Usuário Teste"
        self.email = "teste@email.com"
        self.telefone = "11999999999"
        self.cidade = "São Paulo"
        self.estado = "SP"
        self.senha = "senha_antiga"
        self.foto_perfil = "foto_antiga.png"
        self.tipo = "produtor"