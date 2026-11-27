"""
Teste de desempenho das avaliações (AgroLink) - Locust.

Endpoints testados no back publicado na Azure:
  GET /produtores/{id}  -> perfil público do produtor (média, distribuição, comentários)
  GET /produtos         -> marketplace (mostra a média de cada produtor)

O e-mail e a senha da conta de teste são pedidos uma vez no terminal
(não ficam salvos no arquivo).
"""
import getpass
import os

from locust import HttpUser, task, between

EMAIL = os.environ.get("AGROLINK_EMAIL") or input("E-mail da conta de teste: ")
SENHA = os.environ.get("AGROLINK_SENHA") or getpass.getpass("Senha: ")
TIPO = os.environ.get("AGROLINK_TIPO", "estabelecimento")
PRODUTOR_ID = os.environ.get("AGROLINK_PRODUTOR_ID", "1")

# Guarda as variáveis para os processos seguintes não perguntarem de novo
os.environ["AGROLINK_EMAIL"] = EMAIL
os.environ["AGROLINK_SENHA"] = SENHA


class Estabelecimento(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        r = self.client.post("/login", json={"email": EMAIL, "senha": SENHA, "tipo": TIPO}, name="/login")
        if r.status_code != 200:
            raise RuntimeError(f"Login falhou: {r.status_code}")

    @task(3)
    def perfil_publico(self):
        self.client.get(f"/produtores/{PRODUTOR_ID}", name="/produtores/{id}")

    @task(2)
    def marketplace(self):
        self.client.get("/produtos", name="/produtos")
