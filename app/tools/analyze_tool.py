from langchain_core.tools import tool

from app.services.ai import completion_with_system
from app.config import settings


@tool
def analyze_content(topic: str, content: str) -> str:
    """分析收集到的信息与调研主题的相关性，评估信息充分性。返回评估结果和缺口分析。"""
    system_prompt = """你是一个信息分析专家。分析给定的信息是否足以撰写一份关于指定主题的调研报告。

请评估：
1. 覆盖度评分（1-10分）
2. 已覆盖的关键方面
3. 信息缺口（缺少哪些方面的信息）
4. 是否需要补充搜索（是/否）
5. 如需补充，建议的搜索关键词（每行一个）

请用以下格式输出：
覆盖度: X/10
已覆盖: ...
缺口: ...
需要补充: 是/否
建议关键词: ..."""

    user_prompt = f"""调研主题: {topic}

收集到的信息:
{content[:8000]}"""

    return completion_with_system(
        model=settings.evaluator_model,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.1,
    )
