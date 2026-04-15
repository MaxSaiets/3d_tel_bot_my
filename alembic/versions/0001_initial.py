"""Initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-04-14
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Pure SQL migration — no SQLAlchemy Enum objects to avoid create_type issues with asyncpg
    op.execute("""
        CREATE TYPE IF NOT EXISTS orderstatus AS ENUM ('pending', 'submitted', 'failed');
        CREATE TYPE IF NOT EXISTS crmeventstatus AS ENUM ('pending', 'sent', 'failed');
        CREATE TYPE IF NOT EXISTS supportsessionstatus AS ENUM ('active', 'closed');
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          SERIAL PRIMARY KEY,
            telegram_user_id BIGINT NOT NULL,
            username    VARCHAR(255),
            first_name  VARCHAR(255),
            last_name   VARCHAR(255),
            phone       VARCHAR(32),
            created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE UNIQUE INDEX IF NOT EXISTS ix_users_telegram_user_id ON users(telegram_user_id);
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS start_attributions (
            id          SERIAL PRIMARY KEY,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            source_code VARCHAR(128) NOT NULL,
            created_at  TIMESTAMPTZ NOT NULL
        );
        CREATE INDEX IF NOT EXISTS ix_start_attributions_user_id ON start_attributions(user_id);
        CREATE INDEX IF NOT EXISTS ix_start_attributions_source_code ON start_attributions(source_code);
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id              SERIAL PRIMARY KEY,
            order_uuid      UUID NOT NULL,
            user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            source_code     VARCHAR(128),
            customer_name   VARCHAR(255) NOT NULL,
            customer_phone  VARCHAR(64) NOT NULL,
            delivery_info   TEXT NOT NULL,
            total_amount    NUMERIC(10,2) NOT NULL,
            status          orderstatus NOT NULL DEFAULT 'pending',
            created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT orders_order_uuid_key UNIQUE (order_uuid)
        );
        CREATE INDEX IF NOT EXISTS ix_orders_user_id ON orders(user_id);
        CREATE INDEX IF NOT EXISTS ix_orders_source_code ON orders(source_code);
        CREATE INDEX IF NOT EXISTS ix_orders_status ON orders(status);
        CREATE INDEX IF NOT EXISTS ix_orders_created_at ON orders(created_at);
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id          SERIAL PRIMARY KEY,
            order_id    INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
            sku         VARCHAR(128) NOT NULL,
            qty         INTEGER NOT NULL,
            price       NUMERIC(10,2) NOT NULL
        );
        CREATE INDEX IF NOT EXISTS ix_order_items_order_id ON order_items(order_id);
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS support_sessions (
            id          SERIAL PRIMARY KEY,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            status      supportsessionstatus NOT NULL DEFAULT 'active',
            started_at  TIMESTAMPTZ NOT NULL,
            ended_at    TIMESTAMPTZ,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS ix_support_sessions_user_id ON support_sessions(user_id);
        CREATE INDEX IF NOT EXISTS ix_support_sessions_status ON support_sessions(status);
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS support_message_links (
            id               SERIAL PRIMARY KEY,
            user_id          INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            user_message_id  INTEGER NOT NULL,
            admin_message_id INTEGER NOT NULL,
            created_at       TIMESTAMPTZ NOT NULL,
            CONSTRAINT uq_support_message_admin_msg UNIQUE (admin_message_id)
        );
        CREATE INDEX IF NOT EXISTS ix_support_message_links_user_id ON support_message_links(user_id);
        CREATE INDEX IF NOT EXISTS ix_support_message_links_admin_message_id ON support_message_links(admin_message_id);
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS crm_events (
            id          SERIAL PRIMARY KEY,
            order_id    INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
            payload     JSONB NOT NULL,
            status      crmeventstatus NOT NULL DEFAULT 'pending',
            attempts    INTEGER NOT NULL DEFAULT 0,
            last_error  TEXT,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS ix_crm_events_order_id ON crm_events(order_id);
        CREATE INDEX IF NOT EXISTS ix_crm_events_status ON crm_events(status);
    """)


def downgrade() -> None:
    op.execute("""
        DROP TABLE IF EXISTS crm_events CASCADE;
        DROP TABLE IF EXISTS support_message_links CASCADE;
        DROP TABLE IF EXISTS support_sessions CASCADE;
        DROP TABLE IF EXISTS order_items CASCADE;
        DROP TABLE IF EXISTS orders CASCADE;
        DROP TABLE IF EXISTS start_attributions CASCADE;
        DROP TABLE IF EXISTS users CASCADE;
        DROP TYPE IF EXISTS orderstatus;
        DROP TYPE IF EXISTS crmeventstatus;
        DROP TYPE IF EXISTS supportsessionstatus;
    """)
