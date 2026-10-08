from pydantic import BaseModel


class MensagemCriar(BaseModel):
    negociacao_id: int
    remetente_id: int
    texto: str