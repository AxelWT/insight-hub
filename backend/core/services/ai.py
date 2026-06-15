"""
AI大模型调用客户端
封装 OpenAI 兼容接口调用，支持 DeepSeek 和自定义模型
"""
import logging
import threading

from openai import OpenAI, omit

from core.config import settings

logger = logging.getLogger(__name__)

# 客户端缓存
_clients: dict[str, OpenAI] = {}
_clients_lock = threading.Lock()


def _get_client(model: str) -> tuple[OpenAI, str]:
    if model == "custom":
        if not settings.custom_api_key:
            raise ValueError("自定义模型 API Key 未配置")
        if not settings.custom_base_url:
            raise ValueError("自定义模型 API 地址未配置")

        openai_client = _init_client_with_lock("custom", settings.custom_api_key, settings.custom_base_url)
        model_name = settings.custom_model_name

    elif model == "deepseek":
        if not settings.deepseek_api_key:
            raise ValueError("DeepSeek API Key 未配置")

        openai_client = _init_client_with_lock("deepseek", settings.deepseek_api_key, "https://api.deepseek.com")
        model_name = "deepseek-v4-flash"

    else:
        raise ValueError("不支持该模型")
    return openai_client, model_name


def _init_client_with_lock(cache_key: str, api_key: str, base_url: str) -> OpenAI:
    if cache_key not in _clients:
        with _clients_lock:
            if cache_key not in _clients:
                _clients[cache_key] = OpenAI(api_key=api_key, base_url=base_url)
    return _clients[cache_key]


def _truncate_messages(messages: list[dict], max_chars: int = 80000) -> list[dict]:
    truncation_suffix = "\n...(内容已截断)"

    system_messages = [m for m in messages if m.get("role") == "system"]
    other_messages = [m for m in messages if m.get("role") != "system"]

    total = sum(len(m.get("content", "")) for m in system_messages)
    kept = []

    for m in reversed(other_messages):
        msg_len = len(m.get("content", ""))
        if total + msg_len <= max_chars:
            kept.insert(0, m)
            total += msg_len
        else:
            remaining = max_chars - total - len(truncation_suffix)
            if remaining > 0:
                truncated = m.copy()
                truncated["content"] = m["content"][:remaining] + truncation_suffix
                kept.insert(0, truncated)
            break
    return system_messages + kept


def completion(model: str, messages: list[dict],
               temperature: float = 0.3, max_output_tokens: int = 4096,
               retries: int = 3, return_json: bool = False) -> str:
    for attempt in range(retries + 1):
        try:
            total_chars = sum(len(m.get("content", "")) for m in messages)
            if total_chars > 80000:
                active_messages = _truncate_messages(messages, 80000)
            else:
                active_messages = messages

            client, model_name = _get_client(model)
            response = client.chat.completions.create(model=model_name, messages=active_messages,
                                                      temperature=temperature, max_tokens=max_output_tokens,
                                                      response_format={"type": "json_object"} if return_json == True else omit,
                                                      stream=False)
            return response.choices[0].message.content
        except Exception as e:
            logger.warning(f"Completion attempt {attempt + 1} failed: {e}")
            if attempt == retries:
                logger.error(f"Completion retries failed with '{model}'")
                raise


def completion_with_system(model: str, system_prompt: str, user_prompt: str,
                           temperature: float = 0.3, max_output_tokens: int = 4096) -> str:
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    return completion(model, messages, temperature, max_output_tokens)
