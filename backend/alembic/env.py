"""Alembic 迁移环境配置

配置 Alembic 数据库迁移工具，支持在线和离线两种迁移模式，
适配 SQLite 的 batch 模式（SQLite 不支持 ALTER TABLE 的完整功能）。
"""

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# 导入项目配置和模型
from core.config import settings
from core.database import Base
import core.models  # noqa: F401 - 确保所有模型被加载到 Base.metadata

# Alembic Config 对象，从 alembic.ini 读取配置
config = context.config

# 动态设置数据库 URL（覆盖 alembic.ini 中的配置）
config.set_main_option("sqlalchemy.url", settings.database_url)

# 配置日志（如果配置文件中指定了日志配置）
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 设置 MetaData 用于 autogenerate 支持，使 Alembic 能自动检测模型变更
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """离线模式运行迁移

    不需要数据库连接，仅生成 SQL 脚本。
    适用于需要 DBA 审核后再执行的场景。
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,  # SQLite 需要批处理模式
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """在线模式运行迁移

    直接连接数据库执行迁移语句。
    使用 NullPool 避免连接池干扰迁移操作。
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,  # SQLite 需要批处理模式
        )

        with context.begin_transaction():
            context.run_migrations()


# 根据运行环境选择迁移模式
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
