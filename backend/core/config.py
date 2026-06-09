"""应用配置模块

使用 Pydantic Settings 从环境变量和 .env 文件中加载配置，
支持 DeepSeek、自定义 OpenAI 兼容模型等多种 AI 供应商。
"""

from pydantic_settings import BaseSettings
from pathlib import Path

# 获取项目根目录（backend 的上级目录），用于定位 .env 文件
ROOT_DIR = Path(__file__).parent.parent.parent


class Settings(BaseSettings):
    """应用全局配置类

    所有配置项均可通过环境变量或 .env 文件设置，
    变量名与属性名一致（大小写不敏感）。
    """

    # Tavily 搜索 API 密钥，用于联网搜索
    tavily_api_key: str = ""

    # DeepSeek API 密钥，用于 AI 文本生成
    deepseek_api_key: str = ""

    # 自定义模型配置（OpenAI 兼容接口，可接入任意兼容 API）
    custom_base_url: str = ""  # API 基础地址
    custom_api_key: str = ""  # API 密钥
    custom_model_name: str = ""  # 模型名称

    # Agent 调研参数
    default_model: str = "deepseek"  # 默认使用的模型标识
    evaluator_model: str = "deepseek"  # 评估 Agent 使用的模型
    quick_max_rounds: int = 1  # 快速调研最大搜索轮次
    standard_max_rounds: int = 3  # 标准调研最大搜索轮次
    deep_max_rounds: int = 5  # 深度调研最大搜索轮次
    results_per_round: int = 8  # 每轮搜索返回的结果数
    crawl_timeout: int = 10  # 单个网页爬取超时（秒）
    max_crawl_pages: int = 10  # 单次最多爬取页面数

    # 应用基础配置
    database_url: str = "sqlite:///./data/insight_hub.db"  # SQLite 数据库路径
    report_output_dir: str = "./reports"  # 报告 Markdown 输出目录

    @property
    def available_models(self) -> list[dict]:
        """获取当前可用模型列表

        优先级：自定义模型 > DeepSeek > 默认 DeepSeek
        如果没有配置任何有效模型，返回默认 DeepSeek 选项。
        """
        models = []
        # 自定义模型需要三个配置项同时填写才可用
        if self.custom_base_url and self.custom_api_key and self.custom_model_name:
            models.append({"id": "custom", "name": self.custom_model_name})
        if self.deepseek_api_key:
            models.append({"id": "deepseek", "name": "DeepSeek V4 Flash"})
        # 兜底：无任何有效 API Key 时，仍展示默认选项（前端可渲染，但调用会失败）
        if not models:
            models = [{"id": "deepseek", "name": "DeepSeek V4 Flash"}]
        return models

    def get_max_rounds(self, depth: str) -> int:
        """根据调研深度返回对应的最大搜索轮次"""
        return {
            "quick": self.quick_max_rounds,
            "standard": self.standard_max_rounds,
            "deep": self.deep_max_rounds,
        }.get(depth, self.standard_max_rounds)  # 未知深度默认使用标准轮次

    # Pydantic Settings 配置：从项目根目录 .env 文件读取环境变量
    model_config = {
        "env_file": str(ROOT_DIR / ".env"),
        "env_file_encoding": "utf-8",
    }


# 全局单例配置对象，其他模块通过 from core.config import settings 使用
settings = Settings()

# 启动时确保报告输出目录存在
Path(settings.report_output_dir).mkdir(exist_ok=True)
