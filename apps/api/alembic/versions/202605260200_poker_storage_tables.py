"""create poker import and hand storage tables

Revision ID: 202605260200
Revises: 202605260100
Create Date: 2026-05-26
"""

from collections.abc import Sequence

from alembic import op

revision: str = "202605260200"
down_revision: str | None = "202605260100"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE imports (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            original_filename VARCHAR(255) NOT NULL,
            file_size_bytes BIGINT NOT NULL CHECK (file_size_bytes >= 0),
            file_hash CHAR(64) NOT NULL,
            storage_key VARCHAR(500) NOT NULL,
            source VARCHAR(40) NOT NULL DEFAULT 'pokerstars',
            language VARCHAR(10) NOT NULL DEFAULT 'pt-BR',
            status VARCHAR(20) NOT NULL DEFAULT 'pending'
                CHECK (
                    status IN ('pending','uploaded','processing','succeeded','partial','failed')
                ),
            total_hands_detected INT NULL,
            total_hands_imported INT NULL DEFAULT 0,
            total_hands_duplicate INT NULL DEFAULT 0,
            total_errors INT NULL DEFAULT 0,
            started_at TIMESTAMPTZ NULL,
            finished_at TIMESTAMPTZ NULL,
            error_message TEXT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (user_id, file_hash)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX imports_user_status_idx
        ON imports(user_id, status, created_at DESC)
        """
    )

    op.execute(
        """
        CREATE TABLE import_errors (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
            import_id UUID NOT NULL REFERENCES imports(id) ON DELETE CASCADE,
            line_start INT NOT NULL CHECK (line_start >= 1),
            line_end INT NOT NULL CHECK (line_end >= line_start),
            raw_excerpt TEXT NOT NULL,
            error_code VARCHAR(60) NOT NULL,
            error_message TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute("CREATE INDEX import_errors_import_idx ON import_errors(import_id)")

    op.execute(
        """
        CREATE TABLE sessions (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            started_at TIMESTAMPTZ NOT NULL,
            ended_at TIMESTAMPTZ NOT NULL,
            total_hands INT NOT NULL DEFAULT 0 CHECK (total_hands >= 0),
            net_profit_cents BIGINT NOT NULL DEFAULT 0,
            currency CHAR(3) NOT NULL DEFAULT 'USD',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute("CREATE INDEX sessions_user_time_idx ON sessions(user_id, started_at DESC)")

    op.execute(
        """
        CREATE TABLE hands (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            import_id UUID NOT NULL REFERENCES imports(id) ON DELETE CASCADE,
            session_id UUID NULL REFERENCES sessions(id) ON DELETE SET NULL,
            site VARCHAR(40) NOT NULL,
            site_hand_id VARCHAR(40) NOT NULL,
            site_tournament_id VARCHAR(40) NULL,
            site_table_name VARCHAR(80) NOT NULL,
            game_type VARCHAR(20) NOT NULL CHECK (game_type IN ('tournament','cash','sng','spin')),
            variant VARCHAR(20) NOT NULL CHECK (variant = 'nlhe'),
            table_max_players SMALLINT NOT NULL CHECK (table_max_players > 0),
            is_heads_up BOOLEAN GENERATED ALWAYS AS (table_max_players = 2) STORED,
            buy_in_cents BIGINT NULL,
            fee_cents BIGINT NULL,
            currency CHAR(3) NOT NULL DEFAULT 'USD',
            level_name VARCHAR(20) NULL,
            small_blind BIGINT NOT NULL CHECK (small_blind >= 0),
            big_blind BIGINT NOT NULL CHECK (big_blind >= 0),
            ante BIGINT NOT NULL DEFAULT 0 CHECK (ante >= 0),
            button_seat SMALLINT NOT NULL,
            hero_seat SMALLINT NULL,
            hero_username VARCHAR(60) NOT NULL,
            played_at TIMESTAMPTZ NOT NULL,
            timezone_at_play VARCHAR(40) NULL,
            board_cards VARCHAR(2)[] NOT NULL DEFAULT ARRAY[]::VARCHAR(2)[],
            pot_total BIGINT NOT NULL DEFAULT 0 CHECK (pot_total >= 0),
            rake BIGINT NOT NULL DEFAULT 0 CHECK (rake >= 0),
            hero_position VARCHAR(8) NULL,
            hero_starting_stack BIGINT NULL,
            hero_hole_cards VARCHAR(2)[] NULL,
            hero_net_cents BIGINT NULL,
            hero_went_to_showdown BOOLEAN NOT NULL DEFAULT false,
            hero_won_at_showdown BOOLEAN NULL,
            h_saw_flop BOOLEAN NOT NULL DEFAULT false,
            h_saw_turn BOOLEAN NOT NULL DEFAULT false,
            h_saw_river BOOLEAN NOT NULL DEFAULT false,
            h_went_to_sd BOOLEAN NOT NULL DEFAULT false,
            h_won_at_sd BOOLEAN NOT NULL DEFAULT false,
            h_vpip BOOLEAN NOT NULL DEFAULT false,
            h_pfr BOOLEAN NOT NULL DEFAULT false,
            h_three_bet BOOLEAN NOT NULL DEFAULT false,
            h_faced_three_bet BOOLEAN NOT NULL DEFAULT false,
            h_folded_to_three_bet BOOLEAN NOT NULL DEFAULT false,
            h_pf_open BOOLEAN NOT NULL DEFAULT false,
            h_postflop_bets SMALLINT NOT NULL DEFAULT 0,
            h_postflop_raises SMALLINT NOT NULL DEFAULT 0,
            h_postflop_calls SMALLINT NOT NULL DEFAULT 0,
            raw_text TEXT NOT NULL,
            parser_version VARCHAR(20) NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (user_id, site, site_hand_id)
        )
        """
    )
    op.execute("CREATE INDEX hands_user_played_idx ON hands(user_id, played_at DESC)")
    op.execute(
        """
        CREATE INDEX hands_user_tournament_idx
        ON hands(user_id, site_tournament_id)
        WHERE site_tournament_id IS NOT NULL
        """
    )
    op.execute("CREATE INDEX hands_user_position_idx ON hands(user_id, hero_position)")
    op.execute("CREATE INDEX hands_user_session_idx ON hands(user_id, session_id)")

    op.execute(
        """
        CREATE TABLE hand_players (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
            hand_id UUID NOT NULL REFERENCES hands(id) ON DELETE CASCADE,
            seat SMALLINT NOT NULL,
            username VARCHAR(60) NOT NULL,
            starting_stack BIGINT NOT NULL CHECK (starting_stack >= 0),
            position VARCHAR(8) NULL,
            is_hero BOOLEAN NOT NULL DEFAULT false,
            sit_out BOOLEAN NOT NULL DEFAULT false,
            posted_blind VARCHAR(10) NULL,
            blind_amount BIGINT NOT NULL DEFAULT 0,
            hole_cards VARCHAR(2)[] NULL,
            went_to_showdown BOOLEAN NOT NULL DEFAULT false,
            won_amount BIGINT NOT NULL DEFAULT 0,
            final_action_street VARCHAR(10) NULL,
            UNIQUE (hand_id, seat),
            UNIQUE (hand_id, username)
        )
        """
    )
    op.execute("CREATE INDEX hand_players_hand_idx ON hand_players(hand_id)")
    op.execute("CREATE INDEX hand_players_user_username_idx ON hand_players(username)")

    op.execute(
        """
        CREATE TABLE actions (
            id BIGSERIAL PRIMARY KEY,
            hand_id UUID NOT NULL REFERENCES hands(id) ON DELETE CASCADE,
            user_id UUID NOT NULL,
            player_id UUID NOT NULL REFERENCES hand_players(id) ON DELETE CASCADE,
            sequence INT NOT NULL,
            street VARCHAR(10) NOT NULL,
            action_type VARCHAR(20) NOT NULL,
            amount BIGINT NOT NULL DEFAULT 0,
            raise_to BIGINT NULL,
            is_all_in BOOLEAN NOT NULL DEFAULT false,
            pot_before BIGINT NOT NULL DEFAULT 0,
            pot_after BIGINT NOT NULL DEFAULT 0,
            UNIQUE (hand_id, sequence)
        )
        """
    )
    op.execute("CREATE INDEX actions_hand_idx ON actions(hand_id, sequence)")
    op.execute("CREATE INDEX actions_user_idx ON actions(user_id)")
    op.execute("CREATE INDEX actions_player_idx ON actions(player_id)")

    op.execute(
        """
        CREATE TABLE pots (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
            hand_id UUID NOT NULL REFERENCES hands(id) ON DELETE CASCADE,
            pot_index SMALLINT NOT NULL,
            amount BIGINT NOT NULL CHECK (amount >= 0),
            rake BIGINT NOT NULL DEFAULT 0 CHECK (rake >= 0),
            winners UUID[] NOT NULL DEFAULT ARRAY[]::UUID[],
            UNIQUE (hand_id, pot_index)
        )
        """
    )
    op.execute("CREATE INDEX pots_hand_idx ON pots(hand_id)")

    for table_name in (
        "imports",
        "sessions",
        "hands",
        "hand_players",
        "actions",
        "pots",
    ):
        op.execute(f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY")

    op.execute(
        """
        CREATE POLICY imports_isolation ON imports
          USING (user_id = NULLIF(current_setting('app.user_id', true), '')::uuid)
          WITH CHECK (user_id = NULLIF(current_setting('app.user_id', true), '')::uuid)
        """
    )
    op.execute(
        """
        CREATE POLICY sessions_isolation ON sessions
          USING (user_id = NULLIF(current_setting('app.user_id', true), '')::uuid)
          WITH CHECK (user_id = NULLIF(current_setting('app.user_id', true), '')::uuid)
        """
    )
    op.execute(
        """
        CREATE POLICY hands_isolation ON hands
          USING (user_id = NULLIF(current_setting('app.user_id', true), '')::uuid)
          WITH CHECK (user_id = NULLIF(current_setting('app.user_id', true), '')::uuid)
        """
    )
    op.execute(
        """
        CREATE POLICY hand_players_isolation ON hand_players
          USING (
            EXISTS (
              SELECT 1 FROM hands
              WHERE hands.id = hand_players.hand_id
                AND hands.user_id = NULLIF(current_setting('app.user_id', true), '')::uuid
            )
          )
          WITH CHECK (
            EXISTS (
              SELECT 1 FROM hands
              WHERE hands.id = hand_players.hand_id
                AND hands.user_id = NULLIF(current_setting('app.user_id', true), '')::uuid
            )
          )
        """
    )
    op.execute(
        """
        CREATE POLICY actions_isolation ON actions
          USING (user_id = NULLIF(current_setting('app.user_id', true), '')::uuid)
          WITH CHECK (user_id = NULLIF(current_setting('app.user_id', true), '')::uuid)
        """
    )
    op.execute(
        """
        CREATE POLICY pots_isolation ON pots
          USING (
            EXISTS (
              SELECT 1 FROM hands
              WHERE hands.id = pots.hand_id
                AND hands.user_id = NULLIF(current_setting('app.user_id', true), '')::uuid
            )
          )
          WITH CHECK (
            EXISTS (
              SELECT 1 FROM hands
              WHERE hands.id = pots.hand_id
                AND hands.user_id = NULLIF(current_setting('app.user_id', true), '')::uuid
            )
          )
        """
    )


def downgrade() -> None:
    for table_name in ("pots", "actions", "hand_players", "hands", "sessions", "imports"):
        op.execute(f"ALTER TABLE {table_name} DISABLE ROW LEVEL SECURITY")

    op.drop_index("pots_hand_idx", table_name="pots")
    op.drop_table("pots")
    op.drop_index("actions_player_idx", table_name="actions")
    op.drop_index("actions_user_idx", table_name="actions")
    op.drop_index("actions_hand_idx", table_name="actions")
    op.drop_table("actions")
    op.drop_index("hand_players_user_username_idx", table_name="hand_players")
    op.drop_index("hand_players_hand_idx", table_name="hand_players")
    op.drop_table("hand_players")
    op.drop_index("hands_user_session_idx", table_name="hands")
    op.drop_index("hands_user_position_idx", table_name="hands")
    op.drop_index("hands_user_tournament_idx", table_name="hands")
    op.drop_index("hands_user_played_idx", table_name="hands")
    op.drop_table("hands")
    op.drop_index("sessions_user_time_idx", table_name="sessions")
    op.drop_table("sessions")
    op.drop_index("import_errors_import_idx", table_name="import_errors")
    op.drop_table("import_errors")
    op.drop_index("imports_user_status_idx", table_name="imports")
    op.drop_table("imports")
