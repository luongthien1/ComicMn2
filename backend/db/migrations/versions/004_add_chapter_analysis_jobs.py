"""add chapter_analysis_jobs table

Revision ID: 004
Revises: 003
Create Date: 2026-07-19
"""

import sqlalchemy as sa
from alembic import op

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "chapter_analysis_jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("chapter_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("ingest_result", sa.JSON(), nullable=True),
        sa.Column("issues", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["chapter_id"], ["chapters.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_chapter_analysis_jobs_id"), "chapter_analysis_jobs", ["id"], unique=False)
    op.create_index(
        "ix_chapter_analysis_jobs_chapter_id", "chapter_analysis_jobs", ["chapter_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_chapter_analysis_jobs_chapter_id", table_name="chapter_analysis_jobs")
    op.drop_index(op.f("ix_chapter_analysis_jobs_id"), table_name="chapter_analysis_jobs")
    op.drop_table("chapter_analysis_jobs")
