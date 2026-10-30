from services import cache_service


def test_invalidar_cache_marketplace_com_sucesso(redis_mock):
    # Substitui o cliente Redis utilizado pelo serviço
    cache_service.redis_client = redis_mock

    cache_service.invalidar_cache_marketplace()

    # Verifica se a chave correta foi removida do Redis
    redis_mock.delete.assert_called_once_with("marketplace")

    # Resultado esperado: cache do marketplace invalidado com sucesso.


def test_invalidar_cache_marketplace_com_erro(redis_mock, capsys):
    # Substitui o cliente Redis utilizado pelo serviço
    cache_service.redis_client = redis_mock

    redis_mock.delete.side_effect = Exception("Erro de conexão")

    resultado = cache_service.invalidar_cache_marketplace()

    # Verifica se a tentativa de exclusão foi realizada
    redis_mock.delete.assert_called_once_with("marketplace")

    # Verifica se a mensagem de erro foi exibida
    captura = capsys.readouterr()

    assert "Erro ao limpar cache Redis:" in captura.out
    assert "Erro de conexão" in captura.out

    # Verifica se a função não propaga a exceção
    assert resultado is None

    # Resultado esperado: erro tratado sem interromper a execução.