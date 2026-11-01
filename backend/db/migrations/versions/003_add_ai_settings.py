"""add ai_settings table (singleton row cấu hình Ollama)

Revision ID: 003
Revises: 002
Create Date: 2026-07-19
"""

import sqlalchemy as sa
from alembic import op

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ollama_endpoint", sa.String(500), nullable=True),
        sa.Column("ollama_model", sa.String(255), nullable=False, server_default="qwen2.5:14b"),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.execute(
        "INSERT INTO ai_settings (id, ollama_endpoint, ollama_model) "
        "VALUES (1, NULL, 'qwen2.5:14b')"
    )


def downgrade() -> None:
    op.drop_table("ai_settings")
