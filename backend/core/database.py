from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from backend.core.config import settings

engine = create_engine(
    settings.database_url,
    echo=False,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
    _migrate_db()


def _migrate_db():
    insp = inspect(engine)
    if "research_tasks" not in insp.get_table_names():
        return
    existing = {col["name"] for col in insp.get_columns("research_tasks")}
    with engine.connect() as conn:
        if "task_type" not in existing:
            conn.execute(
                text(
                    "ALTER TABLE research_tasks ADD COLUMN task_type VARCHAR(20) DEFAULT 'search'"
                )
            )
        if "urls" not in existing:
            conn.execute(
                text("ALTER TABLE research_tasks ADD COLUMN urls JSON DEFAULT '[]'")
            )
        if "questions" not in existing:
            conn.execute(
                text("ALTER TABLE research_tasks ADD COLUMN questions TEXT DEFAULT ''")
            )
        if "crawl_depth" not in existing:
            conn.execute(
                text("ALTER TABLE research_tasks ADD COLUMN crawl_depth INTEGER DEFAULT 1")
            )
        if "max_pages" not in existing:
            conn.execute(
                text("ALTER TABLE research_tasks ADD COLUMN max_pages INTEGER DEFAULT 20")
            )
        conn.commit()
