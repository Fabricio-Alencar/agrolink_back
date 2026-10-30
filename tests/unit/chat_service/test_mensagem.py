import services.chat_service as service
from tests.unit.chat_service.fakes import MensagemFake


def test_criar_mensagem_com_sucesso(banco_chat_mock):
    # Executa a criação de uma mensagem fictícia.
    resultado = service.criar_mensagem(
        banco_chat_mock,
        negociacao_id=10,
        remetente_id=20,
        texto="Olá, tenho interesse no produto."
    )

    assert resultado.negociacao_id == 10
    assert resultado.remetente_id == 20
    assert resultado.texto == "Olá, tenho interesse no produto."

    banco_chat_mock.add.assert_called_once_with(resultado)        # Verifica se a mensagem foi adicionada à sessão do banco.
    banco_chat_mock.commit.assert_called_once()                   # Verifica se o commit foi executado.
    banco_chat_mock.refresh.assert_called_once_with(resultado)    # Verifica se o refresh foi executado para atualizar o objeto.


def test_buscar_mensagens_com_sucesso(banco_chat_mock):
    # Cria mensagens fictícias para simular o retorno do banco.
    mensagens = [
        MensagemFake(id=1, negociacao_id=10, texto="Olá"),
        MensagemFake(id=2, negociacao_id=10, texto="Tudo bem?")
    ]

    # Configura a consulta para retornar as mensagens fictícias.
    query_mock = banco_chat_mock.query.return_value
    query_mock.filter.return_value.order_by.return_value.all.return_value = mensagens

    resultado = service.buscar_mensagens(banco_chat_mock, 10)

    # Verifica se as mensagens retornadas são as esperadas.
    assert resultado == mensagens

    # Verifica se a consulta foi realizada na tabela Mensagem.
    banco_chat_mock.query.assert_called_once_with(service.Mensagem)
    # Verifica se o método all() foi executado.
    query_mock.filter.return_value.order_by.return_value.all.assert_called_once()


def test_buscar_mensagens_sem_resultados(banco_chat_mock):
    query_mock = banco_chat_mock.query.return_value
    query_mock.filter.return_value.order_by.return_value.all.return_value = []

    resultado = service.buscar_mensagens(banco_chat_mock, 999)
    # Verifica se nenhuma mensagem foi encontrada.
    assert resultado == []    

def test_marcar_mensagens_como_lidas_com_sucesso(banco_chat_mock):
    mensagens = [
        MensagemFake(id=1, remetente_id=30, lida=False),
        MensagemFake(id=2, remetente_id=40, lida=False)
    ]

    # Configura a consulta para retornar as mensagens não lidas.
    query_mock = banco_chat_mock.query.return_value
    query_mock.filter.return_value.all.return_value = mensagens

    resultado = service.marcar_mensagens_como_lidas(
        banco_chat_mock, 10, 20
    )

    # Verifica se todas as mensagens retornadas foram marcadas como lidas.
    assert all(mensagem.lida is True for mensagem in mensagens)

    # Verifica se a função retornou as mensagens atualizadas.
    assert resultado == mensagens

    # Verifica se as alterações foram salvas.
    banco_chat_mock.commit.assert_called_once()


def test_marcar_mensagens_como_lidas_sem_mensagens(banco_chat_mock):
    # Configura a consulta para não encontrar mensagens pendentes de leitura.
    query_mock = banco_chat_mock.query.return_value
    query_mock.filter.return_value.all.return_value = []

    # Executa a função.
    resultado = service.marcar_mensagens_como_lidas(
        banco_chat_mock, 10, 20
    )

    # Verifica se o resultado é uma lista vazia.
    assert resultado == []

    # Verifica se o commit foi executado.
    banco_chat_mock.commit.assert_called_once()

def test_buscar_ultima_mensagem_com_sucesso(banco_chat_mock):
    # Cria uma mensagem fictícia para representar a mais recente.
    mensagem = MensagemFake(
        id=2,
        negociacao_id=10,
        texto="Tenho interesse."
    )

    # Configura a consulta para retornar essa mensagem.
    query_mock = banco_chat_mock.query.return_value
    query_mock.filter.return_value.order_by.return_value.first.return_value = mensagem

    # Executa a busca da última mensagem.
    resultado = service.buscar_ultima_mensagem(banco_chat_mock, 10)

    # Verifica se a mensagem retornada é a esperada.
    assert resultado == mensagem

    # Verifica se a consulta foi feita na tabela Mensagem.
    banco_chat_mock.query.assert_called_once_with(service.Mensagem)

    # Verifica se first() foi executado.
    query_mock.filter.return_value.order_by.return_value.first.assert_called_once()


def test_buscar_ultima_mensagem_inexistente(banco_chat_mock):
    query_mock = banco_chat_mock.query.return_value
    query_mock.filter.return_value.order_by.return_value.first.return_value = None
    resultado = service.buscar_ultima_mensagem(banco_chat_mock, 999)
    assert resultado is None



def test_contar_mensagens_nao_lidas_com_sucesso(banco_chat_mock):
    query_mock = banco_chat_mock.query.return_value
    query_mock.filter.return_value.count.return_value = 3

    # Executa a contagem para o usuário 20/negociação 10.
    resultado = service.contar_mensagens_nao_lidas(
        banco_chat_mock, 10, 20
    )
    assert resultado == 3
    query_mock.filter.return_value.count.assert_called_once()    # Verifica se count() foi executado.



def test_contar_mensagens_nao_lidas_sem_resultados(banco_chat_mock):
    query_mock = banco_chat_mock.query.return_value
    query_mock.filter.return_value.count.return_value = 0

    resultado = service.contar_mensagens_nao_lidas(
        banco_chat_mock, 10, 20
    )

    # Verifica se nenhuma mensagem não lida foi encontrada.
    assert resultado == 0      