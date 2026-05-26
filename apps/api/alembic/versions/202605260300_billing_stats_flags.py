"""create billing stats and feature flag tables

Revision ID: 202605260300
Revises: 202605260200
Create Date: 2026-05-26
"""

from collections.abc import Sequence

from alembic import op

revision: str = "202605260300"
down_revision: str | None = "202605260200"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE subscriptions (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            stripe_customer_id VARCHAR(60) NOT NULL,
            stripe_subscription_id VARCHAR(60) UNIQUE,
            plan VARCHAR(20) NOT NULL CHECK (plan IN ('free','pro')),
            status VARCHAR(30) NOT NULL,
            current_period_start TIMESTAMPTZ NULL,
            current_period_end TIMESTAMPTZ NULL,
            cancel_at_period_end BOOLEAN NOT NULL DEFAULT false,
            canceled_at TIMESTAMPTZ NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute("CREATE INDEX sub_user_idx ON subscriptions(user_id)")

    op.execute(
        """
        CREATE TABLE webhook_events (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
            provider VARCHAR(40) NOT NULL,
            event_id VARCHAR(255) NOT NULL,
            event_type VARCHAR(80) NOT NULL,
            received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            processed_at TIMESTAMPTZ NULL,
            payload JSONB NOT NULL,
            UNIQUE (provider, event_id)
        )
        """
    )

    op.execute(
        """
        CREATE TABLE stats_snapshots (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            scope_hash CHAR(64) NOT NULL,
            scope_json JSONB NOT NULL,
            metrics JSONB NOT NULL,
            sample_hands INT NOT NULL CHECK (sample_hands >= 0),
            computed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (user_id, scope_hash)
        )
        """
    )
    op.execute("CREATE INDEX stats_user_idx ON stats_snapshots(user_id)")

    op.execute(
        """
        CREATE TABLE feature_flags (
            key VARCHAR(80) PRIMARY KEY,
            description TEXT NULL,
            default_value JSONB NOT NULL DEFAULT 'false'::jsonb,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute(
        """
        CREATE TABLE feature_flag_overrides (
            flag_key VARCHAR(80) NOT NULL REFERENCES feature_flags(key) ON DELETE CASCADE,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            value JSONB NOT NULL,
            PRIMARY KEY (flag_key, user_id)
        )
        """
    )

    op.execute(
        """
        INSERT INTO feature_flags (key, description, default_value)
        VALUES
          ('imports.enabled', 'Enable hand history imports', 'true'::jsonb),
          ('billing.enabled', 'Enable paid billing flows', 'false'::jsonb),
          ('stats.snapshots.enabled', 'Enable persisted stats snapshots', 'false'::jsonb)
        """
    )

    for table_name in ("subscriptions", "stats_snapshots", "feature_flag_overrides"):
        op.execute(f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY")

    op.execute(
        """
        CREATE POLICY subscriptions_isolation ON subscriptions
          USING (user_id = NULLIF(current_setting('app.user_id', true), '')::uuid)
          WITH CHECK (user_id = NULLIF(current_setting('app.user_id', true), '')::uuid)
        """
    )
    op.execute(
        """
        CREATE POLICY stats_snapshots_isolation ON stats_snapshots
          USING (user_id = NULLIF(current_setting('app.user_id', true), '')::uuid)
          WITH CHECK (user_id = NULLIF(current_setting('app.user_id', true), '')::uuid)
        """
    )
    op.execute(
        """
        CREATE POLICY feature_flag_overrides_isolation ON feature_flag_overrides
          USING (user_id = NULLIF(current_setting('app.user_id', true), '')::uuid)
          WITH CHECK (user_id = NULLIF(current_setting('app.user_id', true), '')::uuid)
        """
    )


def downgrade() -> None:
    for table_name in ("feature_flag_overrides", "stats_snapshots", "subscriptions"):
        op.execute(f"ALTER TABLE {table_name} DISABLE ROW LEVEL SECURITY")

    op.drop_table("feature_flag_overrides")
    op.drop_table("feature_flags")
    op.drop_index("stats_user_idx", table_name="stats_snapshots")
    op.drop_table("stats_snapshots")
    op.drop_table("webhook_events")
    op.drop_index("sub_user_idx", table_name="subscriptions")
    op.drop_table("subscriptions")
