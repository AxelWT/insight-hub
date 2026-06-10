"""AI 大模型调用服务

封装 OpenAI 兼容接口调用，支持 DeepSeek 和自定义模型，
提供普通补全、JSON 格式输出、消息截断等能力。
"""

import logging
import threading

from openai import OpenAI

from core.config import settings

logger = logging.getLogger(__name__)

# 客户端缓存，避免每次调用都创建新实例
_clients: dict[str, OpenAI] = {}
_clients_lock = threading.Lock()  # 保护 _clients 的线程锁


def _get_client(model: str) -> tuple[OpenAI, str]:
    """根据模型 ID 返回对应的 API 客户端和实际模型名

    使用缓存复用客户端实例，避免重复创建连接。
    使用双重检查锁定（Double-Checked Locking）确保线程安全。

    Args:
        model: 模型标识，"custom" 使用自定义配置，其他使用 DeepSeek
    Returns:
        (OpenAI 客户端实例, 实际模型名称)
    Raises:
        ValueError: 当 API Key 未配置时
    """
    if model == "custom":
        if not settings.custom_api_key:
            raise ValueError("自定义模型 API Key 未配置")
        if not settings.custom_base_url:
            raise ValueError("自定义模型 API 地址未配置")

        cache_key = "custom"
        # 双重检查锁定：先检查无锁，再检查有锁
        if cache_key not in _clients:
            with _clients_lock:
                if cache_key not in _clients:
                    _clients[cache_key] = OpenAI(
                        api_key=settings.custom_api_key,
                        base_url=settings.custom_base_url,
                    )
        return _clients[cache_key], settings.custom_model_name
    else:
        if not settings.deepseek_api_key:
            raise ValueError("DeepSeek API Key 未配置")

        cache_key = "deepseek"
        # 双重检查锁定：先检查无锁，再检查有锁
        if cache_key not in _clients:
            with _clients_lock:
                if cache_key not in _clients:
                    _clients[cache_key] = OpenAI(
                        api_key=settings.deepseek_api_key,
                        base_url="https://api.deepseek.com",
                    )
        return _clients[cache_key], "deepseek-v4-flash"


def _truncate_messages(messages: list[dict], max_chars: int = 80000) -> list[dict]:
    """截断消息列表以适配模型上下文窗口

    策略：保留所有系统消息，从最新的用户/助手消息开始保留，
    直到总字符数达到上限。最早的消息优先被丢弃。
    """
    # 截断标记，预留空间
    truncation_suffix = "\n...(内容已截断)"

    system_messages = [m for m in messages if m.get("role") == "system"]
    other_messages = [m for m in messages if m.get("role") != "system"]

    total = sum(len(m.get("content", "")) for m in system_messages)
    kept = []
    # 从最新消息开始保留（reversed），确保重要上下文不被丢弃
    for msg in reversed(other_messages):
        msg_len = len(msg.get("content", ""))
        if total + msg_len <= max_chars:
            kept.insert(0, msg)
            total += msg_len
        else:
            # 尝试截断当前消息而非直接丢弃
            # 预留截断标记的空间
            remaining = max_chars - total - len(truncation_suffix)
            if remaining > 200:
                truncated = msg.copy()
                truncated["content"] = msg["content"][:remaining] + truncation_suffix
                kept.insert(0, truncated)
            break

    return system_messages + kept


def completion(
    model: str,
    messages: list[dict],
    temperature: float = 0.3,
    max_tokens: int = 4096,
    retries: int = 1,
) -> str:
    """调用大模型进行对话补全

    当消息总长度超过 80000 字符时，自动截断历史消息以适配上下文窗口。
    支持重试机制，应对网络波动或临时限流。

    Args:
        model: 模型标识
        messages: 对话消息列表，每条包含 role 和 content
        temperature: 生成随机性（0-1，越低越确定）
        max_tokens: 最大生成 token 数
        retries: 失败重试次数
    Returns:
        模型生成的文本内容
    Raises:
        Exception: 所有重试都失败后抛出最后一个异常
    """
    for attempt in range(retries + 1):
        try:
            # 检查消息总长度，超限时截断以避免 API 报错
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


def completion_with_system(
    model: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.3,
    max_tokens: int = 4096,
) -> str:
    """便捷方法：使用系统提示词 + 用户消息进行补全

    适用于大多数单轮对话场景，如文本生成、分析评估等。
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    return completion(model, messages, temperature, max_tokens)


def completion_json(
    model: str,
    messages: list[dict],
    temperature: float = 0.1,
    max_tokens: int = 4096,
    retries: int = 1,
) -> str:
    """调用大模型并要求 JSON 格式输出

    temperature 默认更低（0.1），确保输出格式稳定。
    需要模型支持 response_format 参数。

    Args:
        model: 模型标识
        messages: 对话消息列表
        temperature: 生成随机性（默认 0.1，确保格式稳定）
        max_tokens: 最大生成 token 数
        retries: 失败重试次数
    Returns:
        JSON 格式的字符串
    Raises:
        Exception: 所有重试都失败后抛出最后一个异常
    """
    for attempt in range(retries + 1):
        try:
            # 检查消息总长度，超限时截断以避免 API 报错
            total_chars = sum(len(m.get("content", "")) for m in messages)
            if total_chars > 80000:
                messages = _truncate_messages(messages, max_chars=80000)

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
        except Exception as e:
            logger.warning(f"Completion JSON attempt {attempt + 1} failed: {e}")
            if attempt == retries:
                raise
