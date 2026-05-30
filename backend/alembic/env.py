from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# 导入项目配置和模型
from core.config import settings
from core.database import Base
import core.models  # noqa: F401 - 确保所有模型被加载

# Alembic Config 对象
config = context.config

# 动态设置数据库 URL
config.set_main_option("sqlalchemy.url", settings.database_url)

# 日志配置
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 设置 MetaData 用于 autogenerate 支持
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """离线模式运行迁移（不需要数据库连接）"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,  # SQLite 需要
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """在线模式运行迁移（需要数据库连接）"""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,  # SQLite 需要
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
