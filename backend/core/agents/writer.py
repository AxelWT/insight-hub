"""
写作 Agent - 撰写调研报告
基于搜索结果和爬取内容，利用大模型生成结构化的中文调研报告。
如果主生成流程失败，会自动回退到简化版报告。
"""

import logging
import re

from core.graph.state import ResearchState
from core.services.ai import completion_with_system

logger = logging.getLogger(__name__)

# 备用报告中每条摘要的最大长度
_FALLBACK_SNIPPET_MAX_LEN = 500
# 材料中正文截取的最大长度
_MATERIAL_CONTENT_MAX_LEN = 3000
# 传给 AI 的材料总长度上限
_MATERIALS_TOTAL_MAX_LEN = 12000


def _is_garbled(text: str) -> bool:
    """检测文本是否为乱码（编码错误导致的不可读文本）

    综合判断逻辑：
    1. 统计非 ASCII 字符中，能组成常见中文/日韩字符的比例
    2. 检测常见的乱码模式（如连续的特殊字符、异常字符组合）
    3. 检测重复字符和异常字符频率
    """
    if not text or len(text) < 10:
        return False

    non_ascii = [c for c in text if ord(c) > 127]
    if not non_ascii:
        return False

    # 中文字符范围：CJK 统一汉字 + 扩展
    cjk_ranges = (
        (0x4E00, 0x9FFF),  # CJK 基本
        (0x3400, 0x4DBF),  # CJK 扩展 A
        (0x3000, 0x303F),  # CJK 符号和标点
        (0xFF00, 0xFFEF),  # 全角字符
        (0x2000, 0x206F),  # 常用标点
        (0x0400, 0x04FF),  # 西里尔字母（俄语等）
        (0x0370, 0x03FF),  # 希腊字母
        (0x0600, 0x06FF),  # 阿拉伯字母
        (0x0590, 0x05FF),  # 希伯来字母
    )

    def is_valid_char(c: str) -> bool:
        cp = ord(c)
        return any(lo <= cp <= hi for lo, hi in cjk_ranges)

    valid_count = sum(1 for c in non_ascii if is_valid_char(c))
    ratio = valid_count / len(non_ascii)

    # 如果有效字符占比低于 30%，判定为乱码
    if ratio < 0.3:
        return True

    # 检测常见的乱码模式
    garbled_patterns = [
        r"[^\x00-\x7F]{10,}",  # 连续的非 ASCII 字符
        r"[\x80-\xFF]{5,}",  # 连续的高位字节
        r"[^\w\s]{20,}",  # 连续的特殊字符
    ]

    for pattern in garbled_patterns:
        if re.search(pattern, text):
            return True

    # 检测重复字符（可能是编码错误导致的重复）
    if re.search(r"(.)\1{5,}", text):
        return True

    return False


def _clean_text(text: str, max_len: int = 2000) -> str:
    """清理爬取内容中的噪音，使其可读

    - 移除 HTML 标签残留
    - 移除 JavaScript 和 CSS 代码
    - 移除导航/页脚/版权信息
    - 移除特殊字符和控制字符
    - 移除连续空行
    - 截断到指定长度
    """
    if not text:
        return ""

    # 移除 HTML 标签残留（包括嵌套标签和属性）
    text = re.sub(r"<[^>]*>", "", text)

    # 移除 JavaScript 代码
    text = re.sub(
        r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE
    )
    text = re.sub(r"javascript\s*:", "", text, flags=re.IGNORECASE)

    # 移除 CSS 样式
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"style\s*=\s*[\"'][^\"']*[\"']", "", text, flags=re.IGNORECASE)

    # 移除常见页脚/导航噪音
    noise_patterns = [
        r"版权所有[：:].*",
        r"京公网安备.*",
        r"京ICP备.*",
        r"Copyright\s*©.*",
        r"All\s+Rights?\s+Reserved.*",
        r"建议使用.*浏览器.*",
        r"免责声明.*",
        r"隐私[与和]权限.*",
        r"网站地图.*",
        r"关于我们\s*$",
        r"联系方式\s*$",
        r"网站首页\s*$",
        r"返回顶部\s*$",
        r"ICP.*号[|｜].*",
        r"备案号[：:].*",
        r"网站标识[：:].*",
        r"技术支持[：:].*",
        r"客服电话[：:].*",
        r"服务热线[：:].*",
        r"电子邮箱[：:].*",
        r"邮政编码[：:].*",
        r"地址[：:].*",
        r"电话[：:].*",
        r"传真[：:].*",
    ]
    for pattern in noise_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    # 移除特殊字符和控制字符（保留中文标点和常用符号）
    text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)

    # 移除连续的特殊字符（可能是乱码）
    text = re.sub(r"[^\w\s一-鿿　-〿＀-￯]{10,}", " ", text)

    # 移除连续空行，压缩为单个换行
    text = re.sub(r"\n{3,}", "\n\n", text)

    # 移除行首尾多余空白
    lines = [line.strip() for line in text.splitlines()]
    text = "\n".join(line for line in lines if line)

    # 截断
    if len(text) > max_len:
        text = text[:max_len] + "..."

    return text.strip()


def _build_materials(results: list[dict], content: list[dict]) -> str:
    """将搜索结果和爬取内容整理为研究材料文本

    过滤乱码内容，清理噪音，每条材料标注来源编号、标题、URL、摘要和正文。
    """
    parts = []

    # 建立 URL → 正文内容的映射
    url_to_content = {}
    for c in content:
        url_to_content[c.get("url", "")] = c.get("content", "")

    for i, r in enumerate(results, 1):
        title = r.get("title", "无标题")
        url = r.get("url", "")
        snippet = r.get("snippet", "")
        page_content = url_to_content.get(url, "")

        # 过滤乱码的 snippet
        if snippet and _is_garbled(snippet):
            snippet = ""
            logger.debug(f"[_build_materials] 跳过乱码 snippet: {url}")

        # 过滤乱码的正文
        if page_content and _is_garbled(page_content):
            page_content = ""
            logger.debug(f"[_build_materials] 跳过乱码正文: {url}")

        # 清理内容
        snippet = _clean_text(snippet, 500)
        page_content = _clean_text(page_content, _MATERIAL_CONTENT_MAX_LEN)

        if not snippet and not page_content:
            continue  # 跳过没有有效内容的来源

        part = f"[来源{i}] {title}\nURL: {url}"
        if snippet:
            part += f"\n摘要: {snippet}"
        if page_content:
            part += f"\n正文: {page_content}"
        parts.append(part)

    return "\n\n---\n\n".join(parts)


def _generate_fallback_report(
    topic: str, results: list[dict], content: list[dict]
) -> str:
    """备用报告生成：当 AI 生成失败时，用模板拼接简化版报告

    只使用搜索结果的 snippet（摘要），不使用爬取的原始正文（避免格式混乱）。
    """
    lines = [f"# {topic}\n"]
    lines.append("## 摘要\n")

    # 统计有效结果数
    valid_results = [
        r for r in results if r.get("snippet") and not _is_garbled(r.get("snippet", ""))
    ]
    lines.append(f"本报告基于 {len(valid_results)} 条有效搜索结果整理而成。\n")

    # 列出搜索结果摘要
    lines.append("## 一、信息汇总\n")
    for i, r in enumerate(results[:15], 1):
        title = r.get("title", "无标题")
        url = r.get("url", "")
        snippet = r.get("snippet", "")

        # 跳过乱码 snippet
        if _is_garbled(snippet):
            continue

        snippet = _clean_text(snippet, _FALLBACK_SNIPPET_MAX_LEN)
        if not snippet:
            continue

        lines.append(f"### [{i}] {title}\n")
        lines.append(f"{snippet}\n")
        lines.append(f"来源: {url}\n")

    # 列出参考来源
    lines.append("## 参考来源\n")
    for i, r in enumerate(results, 1):
        title = r.get("title", "")
        if title and not _is_garbled(title):
            lines.append(f"- [{i}] {title} - {r.get('url', '')}")

    lines.append("\n> 注：由于生成过程中出现技术问题，本报告为简化版本。")

    return "\n".join(lines)


def writer_agent(state: ResearchState) -> dict:
    """写作 Agent：生成结构化调研报告

    将搜索结果和爬取内容整理为材料，调用大模型生成报告。
    生成失败时回退到模板化简化报告。
    """
    logger.info("[step-5][writer] 节点开始: 撰写调研报告")

    topic = state["topic"]
    description = state.get("description", "")
    results = state.get("search_results", [])
    content = state.get("crawled_content", [])

    logger.info(
        f"[step-5][writer] 调研主题: {topic} | 搜索结果: {len(results)} 条 | 爬取内容: {len(content)} 个"
    )

    # 整理研究材料（自动过滤乱码和噪音）
    materials = _build_materials(results, content)

    try:
        report = _generate_report(
            topic, description, materials, state.get("model", "deepseek")
        )
        # 对报告进行后处理，修复格式问题
        report = _post_process_report(report)
        logger.info(f"[step-5][writer] 报告生成成功: {len(report)} 字符")
    except Exception as e:
        # 主生成流程失败，使用备用方案生成简化版报告
        logger.warning(f"[step-5][writer] 报告生成失败，使用备用方案: {e}")
        report = _generate_fallback_report(topic, results, content)

    log_entry = {
        "agent": "writer",
        "step": "撰写报告",
        "decision": f"基于 {len(content)} 个来源撰写报告",
        "output": f"报告字数: {len(report)}",
    }

    logger.info("[step-5][writer] 节点完成: 报告撰写任务结束")
    return {
        "report": report,
        "current_step": "报告撰写完成",
        "progress": 100,
        "agent_logs": state.get("agent_logs", []) + [log_entry],
    }


def _generate_report(topic: str, description: str, materials: str, model: str) -> str:
    """调用大模型生成结构化调研报告

    要求模型严格基于提供材料撰写，每个论点标注来源编号，
    不得编造内容。
    """
    system_prompt = """你是一个专业的调研报告撰写者。请根据提供的材料撰写一份结构化的调研报告。

报告要求：
1. 必须使用中文
2. 内容必须基于提供的材料，不得编造
3. 每个论点尽量标注来源 [来源N]
4. 如果材料不足以支撑某个观点，请明确说明
5. 报告必须是排版精良的 markdown 格式
6. 如果材料中包含乱码或不可读的文本，请忽略该部分内容
7. 数据和表格请用清晰的 markdown 表格呈现，不要直接复制原始文本
8. 严格遵循 Markdown 语法规范
9. 标题层级清晰，使用正确的标题符号
10. 列表格式统一，使用正确的列表符号
11. 表格格式规范，列对齐，数据清晰
12. 段落之间留有适当的空行
13. 避免使用过于复杂的嵌套结构

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
关键数据和趋势（如有数据），用 markdown 表格呈现

## 四、不同观点
各方的不同看法和争议

## 五、总结与展望
总结性观点和未来趋势

## 参考来源
- [来源1] 标题 - URL
- [来源2] 标题 - URL
...

格式规范：
- 使用标准的 Markdown 语法
- 标题使用 # 号，不要使用其他符号
- 列表使用 - 或 * 号，保持一致
- 表格使用 | 分隔列，使用 --- 分隔表头
- 代码使用 ` 号包裹
- 链接使用 [text](url) 格式
- 图片使用 ![alt](url) 格式
- 引用使用 > 号
- 强调使用 ** 或 * 号
- 删除线使用 ~~ 号"""

    user_prompt = f"调研主题: {topic}"
    if description:
        user_prompt += f"\n补充说明: {description}"
    # 截取前 12000 字符的材料，避免超出模型上下文
    user_prompt += f"\n\n--- 研究材料 ---\n{materials[:_MATERIALS_TOTAL_MAX_LEN]}"

    return completion_with_system(
        model=model,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.3,
        max_output_tokens=6000,
    )


def _post_process_report(report: str) -> str:
    """对生成的报告进行后处理，修复格式问题

    - 修复标题格式
    - 标准化表格格式
    - 修复列表格式
    - 移除多余的空行
    - 修复链接格式
    """
    if not report:
        return report

    # 修复标题格式：确保标题后有空格
    report = re.sub(r"^(#{1,6})([^\s#])", r"\1 \2", report, flags=re.MULTILINE)

    # 修复标题格式：确保标题前有空行
    report = re.sub(r"\n(#{1,6}\s)", r"\n\n\1", report)

    # 标准化表格格式：确保表格行前后有空行
    report = re.sub(r"\n(\|.+\|)\n", r"\n\n\1\n\n", report)

    # 修复表格分隔行：确保分隔行格式正确
    report = re.sub(r"\n(\|[-\s:]+\|)\n", r"\n\1\n", report)

    # 修复列表格式：确保列表项前有空行
    report = re.sub(r"\n([-*]\s)", r"\n\n\1", report)

    # 修复列表格式：确保列表项后有空行
    report = re.sub(r"(\n[-*]\s[^\n]+)\n([^-*\s])", r"\1\n\n\2", report)

    # 移除多余的空行（超过2个连续空行）
    report = re.sub(r"\n{3,}", "\n\n", report)

    # 修复链接格式：确保链接格式正确
    report = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"[\1](\2)", report)

    # 修复代码格式：确保代码块前后有空行
    report = re.sub(r"\n(```[^\n]*\n)", r"\n\n\1", report)
    report = re.sub(r"(```)\n", r"\1\n\n", report)

    # 移除行首尾多余空白
    lines = [line.strip() for line in report.splitlines()]
    report = "\n".join(line for line in lines if line)

    # 确保报告以空行结尾
    if not report.endswith("\n"):
        report += "\n"

    return report
