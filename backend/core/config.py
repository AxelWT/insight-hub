from pydantic_settings import BaseSettings
from pathlib import Path

# 获取项目根目录（backend 的上级目录）
ROOT_DIR = Path(__file__).parent.parent.parent


class Settings(BaseSettings):
    # Tavily
    tavily_api_key: str = ""

    # DeepSeek
    deepseek_api_key: str = ""

    # Custom Model (OpenAI 兼容接口)
    custom_base_url: str = ""
    custom_api_key: str = ""
    custom_model_name: str = ""

    # Agent Settings
    default_model: str = "deepseek"
    evaluator_model: str = "deepseek"
    quick_max_rounds: int = 1
    standard_max_rounds: int = 3
    deep_max_rounds: int = 5
    results_per_round: int = 8
    crawl_timeout: int = 10
    max_crawl_pages: int = 10

    # App
    database_url: str = "sqlite:///./data/insight_hub.db"
    report_output_dir: str = "./reports"

    @property
    def available_models(self) -> list[dict]:
        models = []
        if self.custom_base_url and self.custom_api_key and self.custom_model_name:
            models.append({"id": "custom", "name": self.custom_model_name})
        if self.deepseek_api_key:
            models.append({"id": "deepseek", "name": "DeepSeek V4 Flash"})
        if not models:
            models = [{"id": "deepseek", "name": "DeepSeek V4 Flash"}]
        return models

    def get_max_rounds(self, depth: str) -> int:
        return {
            "quick": self.quick_max_rounds,
            "standard": self.standard_max_rounds,
            "deep": self.deep_max_rounds,
        }.get(depth, self.standard_max_rounds)

    model_config = {
        "env_file": str(ROOT_DIR / ".env"),  # 从项目根目录读取 .env
        "env_file_encoding": "utf-8",
    }


settings = Settings()

Path(settings.report_output_dir).mkdir(exist_ok=True)
