"""数据库连接与会话管理模块

使用 SQLAlchemy 的声明式映射（Declarative Base），
SQLite 作为默认数据库，适合开发和轻量部署。
"""

import logging
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker, DeclarativeBase

from core.config import settings

logger = logging.getLogger(__name__)

# 判断是否为 SQLite 数据库
is_sqlite = settings.database_url.startswith("sqlite")

# 创建数据库引擎
# echo=False 不打印 SQL 语句
# SQLite 需要 check_same_thread=False 允许跨线程使用
engine_kwargs = {
    "echo": False,
}

if is_sqlite:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # 生产环境数据库连接池配置
    engine_kwargs.update(
        {
            "pool_size": 5,  # 连接池保持的连接数
            "max_overflow": 10,  # 最大溢出连接数
            "pool_recycle": 3600,  # 1 小时后回收连接
            "pool_pre_ping": True,  # 使用前检测连接是否有效
        }
    )

engine = create_engine(settings.database_url, **engine_kwargs)

# 会话工厂，每次调用 SessionLocal() 创建一个新的数据库会话
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    """ORM 声明式基类，所有模型类继承此类"""

    pass


def get_db() -> Generator[Session, None, None]:
    """FastAPI 依赖注入：获取数据库会话

    使用 yield 模式确保请求结束后自动关闭会话，
    在路由函数参数中声明 db: Session = Depends(get_db) 即可使用。
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"数据库操作异常，回滚事务: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def init_db() -> None:
    """初始化数据库（创建所有表）

    根据所有继承 Base 的模型类自动建表，
    已存在的表不会重复创建。适用于开发环境或首次运行。
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("数据库表初始化完成")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise
