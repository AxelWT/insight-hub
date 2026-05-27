import logging

from openai import OpenAI

from app.config import settings

logger = logging.getLogger(__name__)


def _get_client(model: str) -> tuple[OpenAI, str]:
    """根据模型ID返回对应的客户端和实际模型名"""
    if model == "custom":
        client = OpenAI(
            api_key=settings.custom_api_key,
            base_url=settings.custom_base_url,
        )
        return client, settings.custom_model_name
    else:
        client = OpenAI(
            api_key=settings.deepseek_api_key,
            base_url="https://api.deepseek.com",
        )
        return client, "deepseek-v4-flash"


def completion(
    model: str,
    messages: list[dict],
    temperature: float = 0.3,
    max_tokens: int = 4096,
    retries: int = 1,
) -> str:
    for attempt in range(retries + 1):
        try:
            total_chars = sum(len(m.get("content", "")) for m in messages)
            if total_chars > 80000:
                messages = _truncate_messages(messages, max_chars=80000)

            client, model_name = _get_client(model)
            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.warning(f"Completion attempt {attempt + 1} failed: {e}")
            if attempt == retries:
                raise
    return ""


def completion_with_system(
    model: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.3,
    max_tokens: int = 4096,
) -> str:
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    return completion(model, messages, temperature, max_tokens)


def completion_json(
    model: str, messages: list[dict], temperature: float = 0.1, max_tokens: int = 4096
) -> str:
    client, model_name = _get_client(model)
    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        response_format={"type": "json_object"},
        stream=False,
    )
    return response.choices[0].message.content


def _truncate_messages(messages: list[dict], max_chars: int = 60000) -> list[dict]:
    system_messages = [m for m in messages if m["role"] == "system"]
    other_messages = [m for m in messages if m["role"] != "system"]

    total = sum(len(m.get("content", "")) for m in system_messages)
    kept = []
    for msg in reversed(other_messages):
        msg_len = len(msg.get("content", ""))
        if total + msg_len <= max_chars:
            kept.insert(0, msg)
            total += msg_len
        else:
            remaining = max_chars - total
            if remaining > 200:
                truncated = msg.copy()
                truncated["content"] = msg["content"][:remaining] + "\n...(内容已截断)"
                kept.insert(0, truncated)
            break

    return system_messages + kept


def _fallback_simple_response(messages: list[dict]) -> str:
    for m in reversed(messages):
        if m["role"] == "user":
            return f"由于技术原因，无法生成完整回复。关于您的问题「{m['content'][:100]}」，请稍后重试。"
    return "由于技术原因，无法生成回复。请稍后重试。"
