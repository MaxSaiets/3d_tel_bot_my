"""Add chat_messages table

Revision ID: 0002_chat_messages
Revises: 0001_initial
Create Date: 2026-04-15
"""

from alembic import op

revision = "0002_chat_messages"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS chat_messages (
            id          SERIAL PRIMARY KEY,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            content     TEXT    NOT NULL,
            direction   VARCHAR(10) NOT NULL DEFAULT 'user',
            created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_chat_messages_user_id ON chat_messages(user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_chat_messages_created_at ON chat_messages(created_at)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS chat_messages")
