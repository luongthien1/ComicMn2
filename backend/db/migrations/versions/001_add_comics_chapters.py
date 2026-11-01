"""add comics and chapters tables

Revision ID: 001
Revises:
Create Date: 2026-05-16
"""

import sqlalchemy as sa
from alembic import op

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "comics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("author", sa.String(255), nullable=True),
        sa.Column("genres", sa.String(500), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("cover_url", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("ongoing", "completed", "paused", name="comicstatus"),
            nullable=False,
            server_default="ongoing",
        ),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_comics_id"), "comics", ["id"], unique=False)

    op.create_table(
        "chapters",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("comic_id", sa.Integer(), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["comic_id"], ["comics.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_chapters_id"), "chapters", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_chapters_id"), table_name="chapters")
    op.drop_table("chapters")
    op.drop_index(op.f("ix_comics_id"), table_name="comics")
    op.drop_table("comics")
    op.execute("DROP TYPE IF EXISTS comicstatus")
