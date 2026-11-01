"""add chapter content and pages table

Revision ID: 002
Revises: 001
Create Date: 2026-05-17
"""

import sqlalchemy as sa
from alembic import op

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("chapters", sa.Column("content", sa.Text(), nullable=True))

    op.create_table(
        "pages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("chapter_id", sa.Integer(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("image_url", sa.String(1000), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["chapter_id"], ["chapters.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_pages_id"), "pages", ["id"], unique=False)
    op.create_index("ix_pages_chapter_id", "pages", ["chapter_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_pages_chapter_id", table_name="pages")
    op.drop_index(op.f("ix_pages_id"), table_name="pages")
    op.drop_table("pages")
    op.drop_column("chapters", "content")
