"""LangGraph 状态定义

使用 TypedDict 定义调研流程的共享状态，
每个 Agent 节点读取和更新状态中的对应字段。
"""

from typing import TypedDict


class ResearchState(TypedDict, total=False):
    """主题搜索调研流程的状态

    total=False 表示所有字段都是可选的，
    因为不同阶段的状态字段会逐步填充。
    """

    topic: str  # 调研主题
    description: str  # 补充说明
    model: str  # AI 模型标识
    depth: str  # 调研深度（quick/standard/deep）
    max_rounds: int  # 最大搜索轮次
    search_rounds: int  # 当前已完成搜索轮次
    search_queries: list[str]  # 主管 Agent 生成的搜索关键词列表
    current_query: str  # 当前正在执行的搜索关键词
    search_results: list[dict]  # 累计搜索结果
    crawled_content: list[dict]  # 累计爬取内容
    evaluation: str  # 评估 Agent 的原始输出文本
    is_sufficient: bool  # 信息是否充分
    suggested_queries: list[str]  # 评估建议的补充搜索关键词
    report: str  # 最终生成的报告内容
    agent_logs: list[dict]  # Agent 执行日志
    current_step: str  # 当前步骤描述（用于前端展示）
    progress: int  # 进度百分比（0-100）
    evaluator_model: str  # 评估 Agent 使用的模型
    error_message: str  # 错误信息
    sources_saved: bool  # 来源是否已保存


class WebsiteResearchState(TypedDict, total=False):
    """网站内容调研流程的状态

    与主题搜索调研不同，网站调研直接爬取指定 URL，
    不需要搜索和评估循环。
    """

    urls: list[str]  # 用户指定的网站 URL 列表
    questions: str  # 用户的调研问题
    model: str  # AI 模型标识
    crawl_depth: int  # 爬取深度（层数）
    max_pages: int  # 最大爬取页面数
    crawled_content: list[dict]  # 爬取成功的内容
    failed_urls: list[dict]  # 爬取失败的 URL 及错误信息
    report: str  # 最终生成的报告内容
    agent_logs: list[dict]  # Agent 执行日志
    current_step: str  # 当前步骤描述
    progress: int  # 进度百分比
    error_message: str  # 错误信息
    sources_saved: bool  # 来源是否已保存
