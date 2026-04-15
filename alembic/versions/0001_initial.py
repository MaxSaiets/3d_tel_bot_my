"""Initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-04-14
"""

from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # asyncpg requires ONE statement per execute() call

    # Enum types (idempotent via DO block)
    op.execute("DO $$ BEGIN CREATE TYPE orderstatus AS ENUM ('pending','submitted','failed'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")
    op.execute("DO $$ BEGIN CREATE TYPE crmeventstatus AS ENUM ('pending','sent','failed'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")
    op.execute("DO $$ BEGIN CREATE TYPE supportsessionstatus AS ENUM ('active','closed'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")

    # users
    op.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id               SERIAL PRIMARY KEY,
            telegram_user_id BIGINT NOT NULL,
            username         VARCHAR(255),
            first_name       VARCHAR(255),
            last_name        VARCHAR(255),
            phone            VARCHAR(32),
            created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at       TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_telegram_user_id ON users(telegram_user_id)")

    # start_attributions
    op.execute("""
        CREATE TABLE IF NOT EXISTS start_attributions (
            id          SERIAL PRIMARY KEY,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            source_code VARCHAR(128) NOT NULL,
            created_at  TIMESTAMPTZ NOT NULL
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_start_attributions_user_id ON start_attributions(user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_start_attributions_source_code ON start_attributions(source_code)")

    # orders
    op.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id             SERIAL PRIMARY KEY,
            order_uuid     UUID NOT NULL,
            user_id        INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            source_code    VARCHAR(128),
            customer_name  VARCHAR(255) NOT NULL,
            customer_phone VARCHAR(64) NOT NULL,
            delivery_info  TEXT NOT NULL,
            total_amount   NUMERIC(10,2) NOT NULL,
            status         orderstatus NOT NULL DEFAULT 'pending',
            created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT orders_order_uuid_key UNIQUE (order_uuid)
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_orders_user_id ON orders(user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_orders_source_code ON orders(source_code)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_orders_status ON orders(status)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_orders_created_at ON orders(created_at)")

    # order_items
    op.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id       SERIAL PRIMARY KEY,
            order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
            sku      VARCHAR(128) NOT NULL,
            qty      INTEGER NOT NULL,
            price    NUMERIC(10,2) NOT NULL
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_order_items_order_id ON order_items(order_id)")

    # support_sessions
    op.execute("""
        CREATE TABLE IF NOT EXISTS support_sessions (
            id         SERIAL PRIMARY KEY,
            user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            status     supportsessionstatus NOT NULL DEFAULT 'active',
            started_at TIMESTAMPTZ NOT NULL,
            ended_at   TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_support_sessions_user_id ON support_sessions(user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_support_sessions_status ON support_sessions(status)")

    # support_message_links
    op.execute("""
        CREATE TABLE IF NOT EXISTS support_message_links (
            id               SERIAL PRIMARY KEY,
            user_id          INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            user_message_id  INTEGER NOT NULL,
            admin_message_id INTEGER NOT NULL,
            created_at       TIMESTAMPTZ NOT NULL,
            CONSTRAINT uq_support_message_admin_msg UNIQUE (admin_message_id)
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_support_message_links_user_id ON support_message_links(user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_support_message_links_admin_message_id ON support_message_links(admin_message_id)")

    # crm_events
    op.execute("""
        CREATE TABLE IF NOT EXISTS crm_events (
            id         SERIAL PRIMARY KEY,
            order_id   INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
            payload    JSONB NOT NULL,
            status     crmeventstatus NOT NULL DEFAULT 'pending',
            attempts   INTEGER NOT NULL DEFAULT 0,
            last_error TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_crm_events_order_id ON crm_events(order_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_crm_events_status ON crm_events(status)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS crm_events CASCADE")
    op.execute("DROP TABLE IF EXISTS support_message_links CASCADE")
    op.execute("DROP TABLE IF EXISTS support_sessions CASCADE")
    op.execute("DROP TABLE IF EXISTS order_items CASCADE")
    op.execute("DROP TABLE IF EXISTS orders CASCADE")
    op.execute("DROP TABLE IF EXISTS start_attributions CASCADE")
    op.execute("DROP TABLE IF EXISTS users CASCADE")
    op.execute("DROP TYPE IF EXISTS orderstatus")
    op.execute("DROP TYPE IF EXISTS crmeventstatus")
    op.execute("DROP TYPE IF EXISTS supportsessionstatus")
