"""init: create all tables

Revision ID: cb1b2b204cea
Revises:
Create Date: 2026-05-30 10:00:45.928791

初始迁移脚本 - 创建所有数据库表
实际建表逻辑由 Base.metadata.create_all 在应用启动时完成，
此迁移脚本为空操作（pass）。
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# Alembic 使用的版本标识符
revision: str = "cb1b2b204cea"
down_revision: Union[str, None] = None  # 首个迁移，无前驱版本
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """升级操作：创建所有表（实际由应用启动时完成）"""
    pass


def downgrade() -> None:
    """降级操作：删除所有表（空操作）"""
    pass
