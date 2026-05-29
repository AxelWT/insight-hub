import logging

from backend.core.graph.state import ResearchState
from backend.core.services.ai import completion_with_system

logger = logging.getLogger(__name__)


def writer_agent(state: ResearchState) -> dict:
    logger.info("[writer] 节点开始: 撰写调研报告")

    topic = state["topic"]
    description = state.get("description", "")
    results = state.get("search_results", [])
    content = state.get("crawled_content", [])

    logger.info(f"[writer] 调研主题: {topic} | 搜索结果: {len(results)} 条 | 爬取内容: {len(content)} 个")

    materials = _build_materials(results, content)

    try:
        report = _generate_report(
            topic, description, materials, state.get("model", "openai/gpt-4o")
        )
        logger.info(f"[writer] 报告生成成功: {len(report)} 字符")
    except Exception as e:
        logger.warning(f"[writer] 报告生成失败，使用备用方案: {e}")
        report = _generate_fallback_report(topic, results, content)

    log_entry = {
        "agent": "writer",
        "step": "撰写报告",
        "decision": f"基于 {len(content)} 个来源撰写报告",
        "output": f"报告字数: {len(report)}",
    }

    logger.info("[writer] 节点完成: 报告撰写任务结束")
    return {
        "report": report,
        "current_step": "报告撰写完成",
        "progress": 100,
        "agent_logs": state.get("agent_logs", []) + [log_entry],
    }


def _generate_report(topic: str, description: str, materials: str, model: str) -> str:
    system_prompt = """你是一个专业的调研报告撰写者。请根据提供的材料撰写一份结构化的调研报告。

报告要求：
1. 必须使用中文
2. 内容必须基于提供的材料，不得编造
3. 每个论点尽量标注来源 [来源N]
4. 如果材料不足以支撑某个观点，请明确说明

报告结构：
# {主题}

## 摘要
一段话概述核心发现（200字以内）

## 一、背景介绍
主题的背景和上下文

## 二、核心发现
### 2.1 发现一
### 2.2 发现二
...

## 三、数据分析
关键数据和趋势（如有数据）

## 四、不同观点
各方的不同看法和争议

## 五、总结与展望
总结性观点和未来趋势

## 参考来源
- [来源1] 标题 - URL
- [来源2] 标题 - URL
..."""

    user_prompt = f"调研主题: {topic}"
    if description:
        user_prompt += f"\n补充说明: {description}"
    user_prompt += f"\n\n--- 研究材料 ---\n{materials[:12000]}"

    return completion_with_system(
        model=model,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.3,
        max_tokens=6000,
    )


def _generate_fallback_report(
    topic: str, results: list[dict], content: list[dict]
) -> str:
    lines = [f"# {topic}\n"]
    lines.append("## 摘要\n")
    lines.append(
        f"本报告基于 {len(results)} 条搜索结果和 {len(content)} 个网页内容整理而成。\n"
    )

    lines.append("## 一、信息汇总\n")
    for i, r in enumerate(results[:15], 1):
        title = r.get("title", "无标题")
        url = r.get("url", "")
        snippet = r.get("snippet", "")
        lines.append(f"### [{i}] {title}\n")
        if snippet:
            lines.append(f"{snippet}\n")
        lines.append(f"来源: {url}\n")

    lines.append("## 参考来源\n")
    for i, r in enumerate(results, 1):
        lines.append(f"- [{i}] {r.get('title', '')} - {r.get('url', '')}")

    lines.append("\n> 注：由于生成过程中出现技术问题，本报告为简化版本。")

    return "\n".join(lines)


def _build_materials(results: list[dict], content: list[dict]) -> str:
    parts = []

    url_to_content = {}
    for c in content:
        url_to_content[c.get("url", "")] = c.get("content", "")

    for i, r in enumerate(results, 1):
        title = r.get("title", "无标题")
        url = r.get("url", "")
        snippet = r.get("snippet", "")
        page_content = url_to_content.get(url, "")

        part = f"[来源{i}] {title}\nURL: {url}\n摘要: {snippet}"
        if page_content:
            part += f"\n正文: {page_content[:3000]}"
        parts.append(part)

    return "\n\n---\n\n".join(parts)
