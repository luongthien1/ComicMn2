"""chapter revisions, notes, float chapter number, unique (comic_id, number)

- chapters.number: integer -> double precision (cho chương ngoại truyện 30.5)
- chapters: thêm notes (ghi chú chương, trước nằm trong localStorage) và updated_at
- unique (comic_id, number): không cho hai chương trùng số trong một truyện
- chapter_revisions: lịch sử nội dung chương, khôi phục được
- ai_settings.ollama_model: cho phép NULL (= dùng giá trị trong .env)

Revision ID: 005
Revises: 004
Create Date: 2026-11-01
"""

import sqlalchemy as sa
from alembic import op

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "chapters",
        "number",
        type_=sa.Float(),
        existing_type=sa.Integer(),
        existing_nullable=False,
        postgresql_using="number::double precision",
    )
    op.add_column("chapters", sa.Column("notes", sa.Text(), nullable=True))
    op.add_column("chapters", sa.Column("updated_at", sa.DateTime(), nullable=True))
    op.execute("UPDATE chapters SET updated_at = created_at WHERE updated_at IS NULL")
    op.create_unique_constraint("uq_chapters_comic_number", "chapters", ["comic_id", "number"])

    op.create_table(
        "chapter_revisions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("chapter_id", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("char_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reason", sa.String(20), nullable=False, server_default="auto"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["chapter_id"], ["chapters.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_chapter_revisions_chapter_created",
        "chapter_revisions",
        ["chapter_id", "created_at"],
        unique=False,
    )

    op.alter_column(
        "ai_settings", "ollama_model", existing_type=sa.String(255), nullable=True
    )
    # Giá trị mặc định cũ chưa từng được người dùng chọn → để NULL, dùng .env
    op.execute(
        "UPDATE ai_settings SET ollama_model = NULL "
        "WHERE ollama_endpoint IS NULL AND ollama_model = 'qwen2.5:14b'"
    )


def downgrade() -> None:
    op.execute("UPDATE ai_settings SET ollama_model = 'qwen2.5:14b' WHERE ollama_model IS NULL")
    op.alter_column(
        "ai_settings", "ollama_model", existing_type=sa.String(255), nullable=False
    )

    op.drop_index("ix_chapter_revisions_chapter_created", table_name="chapter_revisions")
    op.drop_table("chapter_revisions")

    op.drop_constraint("uq_chapters_comic_number", "chapters", type_="unique")
    op.drop_column("chapters", "updated_at")
    op.drop_column("chapters", "notes")
    op.alter_column(
        "chapters",
        "number",
        type_=sa.Integer(),
        existing_type=sa.Float(),
        existing_nullable=False,
        postgresql_using="round(number)::integer",
    )
