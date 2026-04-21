"""Order improvements: full status lifecycle, ttn column, admin_message_links table.

Revision ID: 0003
Revises: 0002
"""
from alembic import op

revision = "0003"
down_revision = "0002_chat_messages"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new enum values (PostgreSQL allows IF NOT EXISTS in newer versions)
    op.execute("ALTER TYPE orderstatus ADD VALUE IF NOT EXISTS 'confirmed'")
    op.execute("ALTER TYPE orderstatus ADD VALUE IF NOT EXISTS 'shipped'")
    op.execute("ALTER TYPE orderstatus ADD VALUE IF NOT EXISTS 'delivered'")
    op.execute("ALTER TYPE orderstatus ADD VALUE IF NOT EXISTS 'cancelled'")

    # Add TTN (tracking number) column to orders
    op.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS ttn VARCHAR(64)")

    # Create admin_message_links: maps admin-group message_id → internal user_id
    # Used so admin can reply to ANY bot message (order notification, custom prompt)
    # and the reply gets forwarded to the correct user.
    op.execute("""
        CREATE TABLE IF NOT EXISTS admin_message_links (
            id           SERIAL PRIMARY KEY,
            user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            admin_message_id BIGINT NOT NULL,
            link_type    VARCHAR(20) NOT NULL DEFAULT 'order',
            created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_aml_msg_id "
        "ON admin_message_links(admin_message_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_aml_user_id "
        "ON admin_message_links(user_id)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS admin_message_links")
    op.execute("ALTER TABLE orders DROP COLUMN IF EXISTS ttn")
    # Note: PostgreSQL doesn't support dropping enum values easily.
