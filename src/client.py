import logging
import os
import re
import time
from typing import Any

import requests
import urllib3
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("feedback_analyzer.client")


def _parse_float_env(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        return float(raw)
    except ValueError:
        logger.warning("Valor inválido para %s; usando padrão %.2f", name, default)
        return default


def _parse_int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        return int(raw)
    except ValueError:
        logger.warning("Valor inválido para %s; usando padrão %d", name, default)
        return default


def get_llm_config() -> dict[str, Any]:
    raw_host = (
        os.getenv("LLM_HOST")
        or os.getenv("LLM_API_BASE_URL")
        or os.getenv("OLLAMA_HOST")
        or os.getenv("LLM_ENDPOINT")
        or "http://localhost:11434"
    ).strip()

    if raw_host and not raw_host.startswith(("http://", "https://")):
        raw_host = f"http://{raw_host}"

    host = raw_host.rstrip("/")

    if host.endswith("/v1/chat/completions"):
        api_url = host
    elif host.endswith("/api/generate"):
        api_url = host.replace("/api/generate", "/v1/chat/completions")
    elif host.endswith("/api/chat"):
        api_url = host.replace("/api/chat", "/v1/chat/completions")
    else:
        api_url = f"{host}/v1/chat/completions"

    api_key = os.getenv("LLM_API_KEY", "").strip()
    model = os.getenv("LLM_MODEL", "qwen3.5:9b-q4_K_M").strip()
    temperature = _parse_float_env("LLM_TEMPERATURE", 0.3)
    max_tokens = _parse_int_env("LLM_MAX_TOKENS", 2048)
    timeout = _parse_float_env("LLM_TIMEOUT", 120.0)
    verify_ssl = os.getenv("LLM_VERIFY_SSL", "false").strip().lower() in (
        "1",
        "true",
        "yes",
        "sim",
    )

    return {
        "api_url": api_url,
        "api_key": api_key,
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "timeout": timeout,
        "verify_ssl": verify_ssl,
    }


def build_feedback_prompt(feedback: str) -> str:
    return (
        f'Feedback do cliente: "{feedback.strip()}"\n\n'
        "Classifique considerando:\n"
        "- Positivo: elogio, satisfação ou experiência favorável.\n"
        "- Negativo: crítica, insatisfação, defeito ou problema.\n"
        "- Misto: reúne pontos positivos e negativos no mesmo relato.\n"
        "- Neutro: relato puramente objetivo/factual (ex.: data/hora de recebimento, conferência de itens), sem elogios nem críticas.\n\n"
        "Responda em português no formato abaixo:\n"
        "Sentimento: [Positivo / Negativo / Neutro / Misto]\n"
        "Resumo: [resumo curto e objetivo em 1 ou 2 frases]"
    )


def _extract_final_content(message: dict[str, Any], finish_reason: Any) -> str:
    raw_content = message.get("content")
    if not raw_content or not str(raw_content).strip():
        logger.warning(
            "Resposta sem content final | finish_reason=%s | keys=%s",
            finish_reason,
            list(message.keys()),
        )
        return "Não foi possível obter a classificação final do modelo. Tente novamente."

    cleaned = re.sub(r"<think>.*?</think>", "", str(raw_content), flags=re.DOTALL).strip()
    if not cleaned:
        logger.warning(
            "Conteúdo restou vazio após remover raciocínio | finish_reason=%s",
            finish_reason,
        )
        return "Não foi possível formatar a resposta final do modelo. Tente novamente."

    return cleaned


def analisar_feedback(feedback: str) -> str:
    if not feedback or not feedback.strip():
        return "Entrada inválida: o feedback não pode estar vazio."

    cfg = get_llm_config()
    if not cfg["verify_ssl"]:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    headers: dict[str, str] = {"Content-Type": "application/json"}
    if cfg["api_key"]:
        headers["Authorization"] = f"Bearer {cfg['api_key']}"

    payload: dict[str, Any] = {
        "model": cfg["model"],
        "messages": [
            {
                "role": "system",
                "content": (
                    "Você é um assistente de análise de feedbacks de e-commerce. "
                    "Classifique o sentimento e resuma o texto de forma clara e direta. "
                    "Use 'Neutro' apenas quando o relato for puramente informativo ou factual, "
                    "sem expressar satisfação ou insatisfação (mesmo que mencione recebimento ou ausência de problemas). "
                    "Use 'Misto' quando houver aspectos positivos e negativos no mesmo feedback."
                ),
            },
            {"role": "user", "content": build_feedback_prompt(feedback)},
        ],
        "temperature": cfg["temperature"],
        "max_tokens": cfg["max_tokens"],
    }

    input_len = len(feedback.strip())
    logger.info(
        "Enviando análise de feedback | modelo=%s | input_len=%d",
        cfg["model"],
        input_len,
    )

    inicio = time.perf_counter()
    try:
        response = requests.post(
            cfg["api_url"],
            json=payload,
            headers=headers,
            timeout=cfg["timeout"],
            verify=cfg["verify_ssl"],
        )
        latencia_ms = (time.perf_counter() - inicio) * 1000
        logger.info(
            "Resposta recebida | status=%d | latencia_ms=%.1f",
            response.status_code,
            latencia_ms,
        )

        if response.status_code == 401:
            return "Erro de Autenticação (401): Verifique a chave de API configurada no ambiente."
        if response.status_code == 429:
            return "Erro de Limite de Requisições (429): Muitas solicitações em sequência. Tente novamente em instantes."
        if response.status_code in (502, 503, 504):
            return f"Serviço Indisponível ({response.status_code}): O gateway do LLM não respondeu a tempo."
        if response.status_code >= 400:
            return f"Erro na API do LLM (HTTP {response.status_code}): Não foi possível concluir a análise."

        data = response.json()
        choices = data.get("choices") or []
        if not choices:
            return "Resposta inesperada da API: nenhum resultado retornado pelo modelo."

        first_choice = choices[0] or {}
        finish_reason = first_choice.get("finish_reason")
        if finish_reason == "length":
            logger.warning("Resposta truncada por limite de tokens (finish_reason=length).")

        message = first_choice.get("message") or {}
        return _extract_final_content(message, finish_reason)

    except requests.exceptions.Timeout:
        latencia_ms = (time.perf_counter() - inicio) * 1000
        logger.warning("Timeout na chamada ao LLM | latencia_ms=%.1f", latencia_ms)
        return (
            f"Erro de Conexão: A API do LLM excedeu o tempo limite ({cfg['timeout']}s)."
        )
    except requests.exceptions.ConnectionError:
        logger.warning("Falha de conexão de rede ao acessar o endpoint do LLM.")
        return "Erro de Rede: Não foi possível conectar ao serviço de LLM. Verifique a rede ou o endereço configurado."
    except ValueError:
        logger.warning("Resposta inválida: corpo retornado não é um JSON válido.")
        return "Erro de Resposta: O serviço retornou um formato inválido."
    except requests.exceptions.RequestException:
        logger.warning("Erro de requisição HTTP ao comunicar com o LLM.")
        return "Erro de Comunicação: Falha ao enviar a requisição para a API do LLM."