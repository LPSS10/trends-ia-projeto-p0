from unittest.mock import MagicMock, patch

import requests

from src.client import analisar_feedback


def test_entrada_vazia_nao_chama_api():
    with patch("src.client.requests.post") as mock_post:
        resultado = analisar_feedback("   ")
        assert "Entrada inválida" in resultado
        mock_post.assert_not_called()


def test_analise_sucesso_com_mock(monkeypatch):
    monkeypatch.setenv("LLM_API_BASE_URL", "https://api.teste.local/v1/chat/completions")
    monkeypatch.setenv("LLM_MODEL", "modelo-teste")
    monkeypatch.setenv("LLM_TEMPERATURE", "0.2")
    monkeypatch.setenv("LLM_MAX_TOKENS", "250")

    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = {
        "choices": [
            {
                "finish_reason": "stop",
                "message": {
                    "content": "1. Positivo\n2. Entrega rápida e produto de ótima qualidade."
                },
            }
        ]
    }

    with patch("src.client.requests.post", return_value=fake_response) as mock_post:
        resultado = analisar_feedback("Chegou antes do prazo e funciona perfeitamente!")

        assert "Positivo" in resultado
        assert "Entrega rápida" in resultado
        mock_post.assert_called_once()
        _, kwargs = mock_post.call_args
        assert kwargs["json"]["model"] == "modelo-teste"
        assert kwargs["json"]["temperature"] == 0.2
        assert kwargs["json"]["max_tokens"] == 250


def test_erro_401_autenticacao(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "chave_invalida")

    fake_response = MagicMock()
    fake_response.status_code = 401

    with patch("src.client.requests.post", return_value=fake_response):
        resultado = analisar_feedback("Produto bom, mas embalagem amassada.")
        assert "Erro de Autenticação (401)" in resultado


def test_erro_timeout_rede():
    with patch(
        "src.client.requests.post",
        side_effect=requests.exceptions.Timeout("Tempo esgotado"),
    ):
        resultado = analisar_feedback("Gostei bastante do atendimento.")
        assert "Erro de Conexão" in resultado
        assert "tempo limite" in resultado