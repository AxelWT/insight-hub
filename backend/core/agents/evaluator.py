"""评估 Agent - 评估信息充分性

分析已收集的搜索结果和爬取内容，判断信息是否足以撰写高质量调研报告，
如果不够充分则建议补充搜索关键词。
"""

import logging

from core.graph.state import ResearchState
from core.services.ai import completion_with_system
from core.config import settings

logger = logging.getLogger(__name__)


def evaluator_agent(state: ResearchState) -> dict:
    """评估 Agent：评估已收集信息的充分性

    从覆盖度、深度、多样性、时效性四个维度评估，
    决定是否需要继续搜索或可以开始撰写报告。
    """
    logger.info("[evaluator] 节点开始: 评估信息充分性")

    topic = state["topic"]
    results = state.get("search_results", [])
    content = state.get("crawled_content", [])
    search_rounds = state.get("search_rounds", 1)
    max_rounds = state.get("max_rounds", 3)

    logger.info(
        f"[evaluator] 当前轮次: {search_rounds}/{max_rounds} | 搜索结果: {len(results)} 条 | 爬取内容: {len(content)} 个"
    )

    # 构建内容摘要供模型评估
    content_summary = _build_content_summary(results, content)

    system_prompt = """你是一个信息评估专家。评估收集到的信息是否足以撰写一份高质量调研报告。

评估维度：
1. **覆盖度**：是否覆盖了主题的各个关键方面
2. **深度**：是否有足够的数据、案例、分析支撑
3. **多样性**：是否有不同来源、不同观点的信息
4. **时效性**：信息是否足够新（对时效性要求高的主题）

请严格按以下格式输出（不要输出其他内容）：

覆盖度: X/10
已覆盖: 用简短词语列出已覆盖的方面
缺口: 用简短词语列出缺少的方面
深度评估: X/10
需要补充: 是 或 否
建议关键词: 如果需要补充，每行一个建议的搜索关键词（要具体有针对性）"""

    user_prompt = f"""调研主题: {topic}
当前搜索轮次: {search_rounds}/{max_rounds}

收集到的信息概要:
{content_summary[:6000]}"""

    response = completion_with_system(
        model=state.get("evaluator_model", settings.evaluator_model),
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.1,  # 低温度确保评估结果稳定
    )

    # 解析评估结果
    is_sufficient = _parse_sufficiency(response)
    suggested = _parse_suggested_queries(response)

    # 是否还能继续搜索（未达到最大轮次）
    can_continue = search_rounds < max_rounds

    logger.info(
        f"[evaluator] 评估结果: {'充分' if is_sufficient else '不充分'} | 可继续搜索: {can_continue}"
    )
    if suggested:
        logger.info(f"[evaluator] 建议关键词: {suggested}")

    log_entry = {
        "agent": "evaluator",
        "step": "评估信息充分性",
        "decision": f"评估结果: {'充分' if is_sufficient else '不充分'}，{'将补充搜索' if not is_sufficient and can_continue else '开始撰写报告'}",
        "output": response,
    }

    logger.info("[evaluator] 节点完成: 信息评估任务结束")
    return {
        "evaluation": response,
        # 如果信息充分，或已无法继续搜索，则判定为充分
        "is_sufficient": is_sufficient or not can_continue,
        # 仅在信息不充分且能继续搜索时提供补充关键词
        "suggested_queries": suggested if not is_sufficient and can_continue else [],
        "current_step": f"信息评估: {'充分，开始撰写' if is_sufficient else '不充分，补充搜索'}",
        "progress": min(state.get("progress", 50) + 10, 75),
        "agent_logs": state.get("agent_logs", []) + [log_entry],
    }


def _build_content_summary(results: list[dict], content: list[dict]) -> str:
    """构建信息概要，供评估模型分析

    将搜索结果和爬取内容整理成文本格式，
    标注哪些结果有正文、哪些仅有摘要。
    """
    parts = []
    url_to_content = {c.get("url", ""): c.get("content", "") for c in content}

    for i, r in enumerate(results[:20], 1):  # 最多展示 20 条
        title = r.get("title", "无标题")
        url = r.get("url", "")
        snippet = r.get("snippet", "")[:300]
        page_content = url_to_content.get(url, "")
        has_full = bool(page_content)
        parts.append(
            f"[{i}] {title} {'(有正文)' if has_full else '(仅摘要)'}: {snippet}"
        )

    if content:
        total_chars = sum(len(c.get("content", "")) for c in content)
        parts.append(f"\n共爬取 {len(content)} 个网页正文，总计约 {total_chars} 字符")

    return "\n".join(parts) if parts else "暂无收集到的信息"


def _parse_sufficiency(evaluation: str) -> bool:
    """从评估文本中解析信息是否充分

    查找"需要补充"关键字，若其后出现"否"则判定为充分。
    """
    for line in evaluation.split("\n"):
        if "需要补充" in line:
            return "否" in line
    return True  # 默认判定为充分


def _parse_suggested_queries(evaluation: str) -> list[str]:
    """从评估文本中解析建议的补充搜索关键词

    查找"建议关键词"标题行，提取后续非空行作为关键词。
    """
    queries = []
    in_suggestions = False
    for line in evaluation.split("\n"):
        if "建议关键词" in line:
            in_suggestions = True
            # 标题行冒号后可能紧跟关键词
            parts = line.split(":", 1)
            if len(parts) > 1 and parts[1].strip():
                queries.append(parts[1].strip())
            continue
        if in_suggestions and line.strip():
            queries.append(line.strip())
    return queries
