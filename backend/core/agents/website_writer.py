import logging

from core.graph.state import WebsiteResearchState
from core.services.ai import completion_with_system

logger = logging.getLogger(__name__)


def website_writer_agent(state: WebsiteResearchState) -> dict:
    logger.info("[website_writer] 节点开始: 撰写网站调研报告")

    questions = state.get("questions", "")
    content = state.get("crawled_content", [])
    failed_urls = state.get("failed_urls", [])

    logger.info(f"[website_writer] 调研问题: {questions[:100] if questions else '无'} | 爬取内容: {len(content)} 个 | 失败 URL: {len(failed_urls)} 个")

    materials = _build_materials(content)

    try:
        report = _generate_report(
            questions, materials, failed_urls, state.get("model", "deepseek")
        )
        logger.info(f"[website_writer] 报告生成成功: {len(report)} 字符")
    except Exception as e:
        logger.warning(f"[website_writer] 报告生成失败，使用备用方案: {e}")
        report = _generate_fallback_report(questions, content, failed_urls)

    log_entry = {
        "agent": "website_writer",
        "step": "撰写报告",
        "decision": f"基于 {len(content)} 个网站内容撰写报告"
        + (f"，{len(failed_urls)} 个网站爬取失败" if failed_urls else ""),
        "output": f"报告字数: {len(report)}",
    }

    logger.info("[website_writer] 节点完成: 网站调研报告撰写结束")
    return {
        "report": report,
        "current_step": "报告撰写完成",
        "progress": 100,
        "agent_logs": state.get("agent_logs", []) + [log_entry],
    }


def _generate_report(
    questions: str, materials: str, failed_urls: list[dict], model: str
) -> str:
    failed_info = ""
    if failed_urls:
        lines = "\n".join(f"- {f['url']}（原因: {f['error']}）" for f in failed_urls)
        failed_info = f"\n\n以下网站爬取失败，无法获取内容：\n{lines}"

    system_prompt = """你是一个专业的网站内容分析专家。用户提供了多个网站的内容，并提出了具体问题。
请结合网站内容，针对用户的问题进行深入分析，撰写调研报告。

要求：
1. 必须使用中文
2. 围绕用户问题组织报告结构，每个问题单独成章
3. 每个分析点必须标注来源 [来源N]，不得编造内容
4. 如有爬取失败的网站，需在报告中说明
5. 对于问题中涉及但网站内容未覆盖的部分，明确指出信息缺口
6. 客观呈现不同网站的观点，如有矛盾之处需指出

报告结构：
# {基于问题生成的标题}

## 摘要
一段话概述核心发现（200字以内）

## 一、问题一：{从用户问题提取}
### 分析
### 关键发现

## 二、问题二：{从用户问题提取}
### 分析
### 关键发现

...（按用户问题逐一展开）

## 综合分析
跨网站对比、趋势总结、矛盾观点分析

## 信息缺口与建议
未覆盖的方面和进一步调研建议

## 参考来源
- [来源1] 标题 - URL
- [来源2] 标题 - URL
..."""

    user_prompt = f"用户问题:\n{questions}"
    user_prompt += f"\n\n--- 网站内容 ---\n{materials[:12000]}"
    if failed_info:
        user_prompt += f"\n\n--- 爬取失败的网站 ---\n{failed_info}"

    return completion_with_system(
        model=model,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.3,
        max_tokens=6000,
    )


def _generate_fallback_report(
    questions: str, content: list[dict], failed_urls: list[dict]
) -> str:
    lines = ["# 网站调研报告\n"]
    lines.append("## 摘要\n")
    lines.append(
        f"本报告基于 {len(content)} 个网站内容整理而成，针对用户提出的问题进行分析。\n"
    )

    if questions:
        lines.append("## 用户问题\n")
        for q in questions.strip().split("\n"):
            if q.strip():
                lines.append(f"- {q.strip()}\n")

    lines.append("## 网站内容汇总\n")
    for i, c in enumerate(content, 1):
        title = c.get("title", "无标题")
        url = c.get("url", "")
        page_content = c.get("content", "")
        lines.append(f"### [来源{i}] {title}\n")
        lines.append(f"URL: {url}\n")
        if page_content:
            lines.append(f"{page_content[:2000]}\n")

    if failed_urls:
        lines.append("## 爬取失败的网站\n")
        for f in failed_urls:
            lines.append(f"- {f['url']}（原因: {f['error']}）\n")

    lines.append("## 参考来源\n")
    for i, c in enumerate(content, 1):
        lines.append(f"- [{i}] {c.get('title', '')} - {c.get('url', '')}")

    lines.append("\n> 注：由于生成过程中出现技术问题，本报告为简化版本。")

    return "\n".join(lines)


def _build_materials(content: list[dict]) -> str:
    parts = []
    for i, c in enumerate(content, 1):
        title = c.get("title", "无标题")
        url = c.get("url", "")
        page_content = c.get("content", "")
        part = f"[来源{i}] {title}\nURL: {url}"
        if page_content:
            part += f"\n正文: {page_content[:3000]}"
        parts.append(part)
    return "\n\n---\n\n".join(parts)
