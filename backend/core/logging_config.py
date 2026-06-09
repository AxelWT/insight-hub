"""日志配置模块

配置三级日志输出：
1. 控制台：INFO 级别，方便开发调试
2. 全量文件：DEBUG 级别，按大小轮转，保留完整日志
3. 错误文件：ERROR 级别，单独记录便于排查

同时降低第三方库的日志级别，避免噪音。
"""

import logging
import logging.handlers
from pathlib import Path

# 有效的日志级别列表
VALID_LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

# 第三方库日志配置
THIRD_PARTY_LOGGERS = {
    "httpx": logging.WARNING,
    "httpcore": logging.WARNING,
    "openai": logging.WARNING,
    "langchain": logging.WARNING,
    "sqlalchemy.engine": logging.WARNING,
}


def setup_logging(log_level: str = "INFO", log_dir: str | Path = "./logs"):
    """配置应用日志

    Args:
        log_level: 控制台日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: 日志文件目录路径，默认为 ./logs

    Raises:
        ValueError: 当 log_level 不是有效的日志级别时
    """
    # 参数验证
    log_level = log_level.upper()
    if log_level not in VALID_LOG_LEVELS:
        raise ValueError(
            f"无效的日志级别: {log_level}，有效值为: {', '.join(VALID_LOG_LEVELS)}"
        )

    # 确保日志目录存在
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    # 统一日志格式：时间 | 级别 | 模块:函数:行号 | 消息
    log_format = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 获取根日志器
    root_logger = logging.getLogger()

    # 清除已有的 handler，避免重复添加
    root_logger.handlers.clear()

    # 配置根日志器级别为 DEBUG，让各 handler 自行过滤
    root_logger.setLevel("DEBUG")

    # 控制台处理器：输出到终端，用于实时查看
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(log_format)
    root_logger.addHandler(console_handler)

    # 全量日志文件处理器：按大小轮转，单文件最大 10MB，保留 5 个备份
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / "app.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel("DEBUG")  # 文件记录所有级别
    file_handler.setFormatter(log_format)
    root_logger.addHandler(file_handler)

    # 错误日志单独文件：仅记录 ERROR 及以上级别，便于快速定位问题
    error_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / "error.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )
    error_handler.setLevel("ERROR")
    error_handler.setFormatter(log_format)
    root_logger.addHandler(error_handler)

    # 降低第三方库日志级别，避免大量 HTTP 请求/响应日志干扰
    for logger_name, level in THIRD_PARTY_LOGGERS.items():
        logging.getLogger(logger_name).setLevel(level)

    logging.info("日志系统初始化完成")
