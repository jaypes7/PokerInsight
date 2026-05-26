# 04 — Modelo de dados

> Schema PostgreSQL completo. Migrações via Alembic. Tudo em snake_case. PKs UUID v7 (lexicograficamente ordenáveis).

---

## 1. Diagrama lógico (alto nível)

```
users ─┬─< user_oauth_accounts
       ├─< refresh_tokens
       ├─< subscriptions ─< invoices
       ├─< imports ─< import_errors
       ├─< sessions  (sessões de poker = bloco temporal)
       │       │
       │       └─< hands ─┬─< hand_players
       │                  ├─< actions
       │                  ├─< board_cards
       │                  └─< pots
       ├─< stats_snapshots  (cache de stats agregadas)
       ├─< feature_flag_overrides
       └─< audit_logs
```

---

## 2. Conventions

- PK: `id UUID PRIMARY KEY DEFAULT uuid_generate_v7()`
- Timestamps: `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`, `updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()` (trigger atualiza)
- Soft delete: coluna `deleted_at TIMESTAMPTZ NULL` em tabelas com PII; default queries via repository filtram `deleted_at IS NULL`
- Enums: ENUM Postgres para conjuntos pequenos e fixos; tabelas de lookup para conjuntos que podem crescer
- Money: armazenar **em cents** como `BIGINT` ou em microcents para precisão; nunca `FLOAT`. Coluna `currency CHAR(3)` ao lado.
- Cards: armazenados como string de 2 chars: rank + suit (ex: `Td`, `Ah`). Order array `['Td','Jc']`.
- Posições: enum `('SB','BB','UTG','UTG1','UTG2','MP','MP1','MP2','LJ','HJ','CO','BTN')`.
- Todo dado de usuário tem `user_id` indexada.

---

## 3. Tabelas

### 3.1 `users`

```sql
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    email           CITEXT NOT NULL UNIQUE,
    email_verified_at TIMESTAMPTZ NULL,
    display_name    VARCHAR(80) NOT NULL,
    password_hash   VARCHAR(255) NULL,                -- argon2id; NULL se só OAuth
    role            VARCHAR(20) NOT NULL DEFAULT 'user',  -- 'user' | 'admin'
    locale          VARCHAR(10) NOT NULL DEFAULT 'pt-BR',
    timezone        VARCHAR(64) NOT NULL DEFAULT 'America/Sao_Paulo',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ NULL,
    last_login_at   TIMESTAMPTZ NULL,
    CHECK (role IN ('user','admin'))
);
CREATE INDEX users_email_active_idx ON users (email) WHERE deleted_at IS NULL;
```

### 3.2 `user_oauth_accounts`

```sql
CREATE TABLE user_oauth_accounts (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider    VARCHAR(40) NOT NULL,         -- 'google'
    provider_user_id VARCHAR(255) NOT NULL,
    email_at_provider CITEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (provider, provider_user_id)
);
CREATE INDEX user_oauth_user_idx ON user_oauth_accounts(user_id);
```

### 3.3 `refresh_tokens`

```sql
CREATE TABLE refresh_tokens (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    user_id      UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash   CHAR(64) NOT NULL UNIQUE,              -- SHA-256 do token opaco
    family_id    UUID NOT NULL,                          -- para reuse detection
    parent_id    UUID NULL REFERENCES refresh_tokens(id),
    user_agent   VARCHAR(255) NULL,
    ip_address   INET NULL,
    issued_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at   TIMESTAMPTZ NOT NULL,
    revoked_at   TIMESTAMPTZ NULL,
    used_at      TIMESTAMPTZ NULL
);
CREATE INDEX refresh_user_active_idx ON refresh_tokens(user_id) WHERE revoked_at IS NULL;
CREATE INDEX refresh_family_idx ON refresh_tokens(family_id);
```

### 3.4 `subscriptions`

```sql
CREATE TABLE subscriptions (
    id                    UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    user_id               UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    stripe_customer_id    VARCHAR(60) NOT NULL,
    stripe_subscription_id VARCHAR(60) UNIQUE,
    plan                  VARCHAR(20) NOT NULL,           -- 'free' | 'pro'
    status                VARCHAR(30) NOT NULL,           -- 'active'|'past_due'|'canceled'|'trialing'|'incomplete'
    current_period_start  TIMESTAMPTZ NULL,
    current_period_end    TIMESTAMPTZ NULL,
    cancel_at_period_end  BOOLEAN NOT NULL DEFAULT false,
    canceled_at           TIMESTAMPTZ NULL,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX sub_user_idx ON subscriptions(user_id);
```

### 3.5 `webhook_events` (idempotência)

```sql
CREATE TABLE webhook_events (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    provider    VARCHAR(40) NOT NULL,    -- 'stripe'
    event_id    VARCHAR(255) NOT NULL,
    event_type  VARCHAR(80) NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processed_at TIMESTAMPTZ NULL,
    payload     JSONB NOT NULL,
    UNIQUE (provider, event_id)
);
```

### 3.6 `imports`

```sql
CREATE TABLE imports (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    original_filename VARCHAR(255) NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    file_hash       CHAR(64) NOT NULL,                 -- SHA-256 do conteúdo
    storage_key     VARCHAR(500) NOT NULL,             -- chave em R2
    source          VARCHAR(40) NOT NULL DEFAULT 'pokerstars',  -- futuro: 'ggpoker'
    language        VARCHAR(10) NOT NULL DEFAULT 'pt-BR',
    status          VARCHAR(20) NOT NULL DEFAULT 'pending',  -- pending|processing|succeeded|partial|failed
    total_hands_detected INT NULL,
    total_hands_imported INT NULL DEFAULT 0,
    total_hands_duplicate INT NULL DEFAULT 0,
    total_errors    INT NULL DEFAULT 0,
    started_at      TIMESTAMPTZ NULL,
    finished_at     TIMESTAMPTZ NULL,
    error_message   TEXT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, file_hash)
);
CREATE INDEX imports_user_status_idx ON imports(user_id, status, created_at DESC);
```

### 3.7 `import_errors`

```sql
CREATE TABLE import_errors (
    id         UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    import_id  UUID NOT NULL REFERENCES imports(id) ON DELETE CASCADE,
    line_start INT NOT NULL,
    line_end   INT NOT NULL,
    raw_excerpt TEXT NOT NULL,                  -- até 2000 chars
    error_code VARCHAR(60) NOT NULL,            -- 'UNKNOWN_TOKEN', 'CHIPS_IMBALANCE', etc.
    error_message TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX import_errors_import_idx ON import_errors(import_id);
```

### 3.8 `sessions`

Bloco lógico que agrupa mãos jogadas continuamente. Útil para "sessão de hoje".

```sql
CREATE TABLE sessions (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    started_at  TIMESTAMPTZ NOT NULL,
    ended_at    TIMESTAMPTZ NOT NULL,
    total_hands INT NOT NULL DEFAULT 0,
    net_profit_cents BIGINT NOT NULL DEFAULT 0,  -- soma de net por mão; pode ser negativo
    currency    CHAR(3) NOT NULL DEFAULT 'USD',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX sessions_user_time_idx ON sessions(user_id, started_at DESC);
```

Sessão é detectada por regra: gap > 60min entre mãos = nova sessão (configurável).

### 3.9 `hands`

Tabela principal. **Particionada por mês** quando volume > 10M.

```sql
CREATE TABLE hands (
    id                   UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    user_id              UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    import_id            UUID NOT NULL REFERENCES imports(id) ON DELETE CASCADE,
    session_id           UUID NULL REFERENCES sessions(id) ON DELETE SET NULL,

    -- Identificação
    site                 VARCHAR(40) NOT NULL,        -- 'pokerstars'
    site_hand_id         VARCHAR(40) NOT NULL,        -- "260820828710"
    site_tournament_id   VARCHAR(40) NULL,            -- "4000776344" ou NULL para cash
    site_table_name      VARCHAR(80) NOT NULL,        -- "4000776344 1"

    -- Tipo de jogo
    game_type            VARCHAR(20) NOT NULL,        -- 'tournament'|'cash'|'sng'|'spin'
    variant              VARCHAR(20) NOT NULL,        -- 'nlhe'  (no limit holdem)
    table_max_players    SMALLINT NOT NULL,           -- 2,6,9
    is_heads_up          BOOLEAN GENERATED ALWAYS AS (table_max_players = 2) STORED,

    -- Buy-in / blinds
    buy_in_cents         BIGINT NULL,                 -- "0.42" → 42 (para tournament)
    fee_cents            BIGINT NULL,                 -- "0.08" → 8
    currency             CHAR(3) NOT NULL DEFAULT 'USD',
    level_name           VARCHAR(20) NULL,            -- 'I','II','III',...
    small_blind          BIGINT NOT NULL,             -- em fichas (não cents) para tournament; em cents para cash
    big_blind            BIGINT NOT NULL,
    ante                 BIGINT NOT NULL DEFAULT 0,

    -- Posicionamento
    button_seat          SMALLINT NOT NULL,
    hero_seat            SMALLINT NULL,
    hero_username        VARCHAR(60) NOT NULL,

    -- Datas
    played_at            TIMESTAMPTZ NOT NULL,
    timezone_at_play     VARCHAR(40) NULL,            -- 'ET' do header

    -- Resultado de jogo
    board_cards          VARCHAR(2)[] NOT NULL DEFAULT ARRAY[]::VARCHAR(2)[],  -- até 5
    pot_total            BIGINT NOT NULL DEFAULT 0,
    rake                 BIGINT NOT NULL DEFAULT 0,

    -- Hero summary
    hero_position        VARCHAR(8) NULL,             -- 'BTN','CO','BB',...
    hero_starting_stack  BIGINT NULL,
    hero_hole_cards      VARCHAR(2)[] NULL,           -- ['Td','Jc']
    hero_net_cents       BIGINT NULL,                 -- ganho/perda nesta mão em cents
    hero_went_to_showdown BOOLEAN NOT NULL DEFAULT false,
    hero_won_at_showdown BOOLEAN NULL,                -- NULL se não foi ao showdown

    -- Raw para auditoria
    raw_text             TEXT NOT NULL,               -- texto original da mão
    parser_version       VARCHAR(20) NOT NULL,

    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (user_id, site, site_hand_id)
);

CREATE INDEX hands_user_played_idx ON hands(user_id, played_at DESC);
CREATE INDEX hands_user_tournament_idx ON hands(user_id, site_tournament_id) WHERE site_tournament_id IS NOT NULL;
CREATE INDEX hands_user_position_idx ON hands(user_id, hero_position);
CREATE INDEX hands_user_session_idx ON hands(user_id, session_id);

-- particionamento futuro (quando crescer):
-- PARTITION BY RANGE (played_at)
```

### 3.10 `hand_players`

```sql
CREATE TABLE hand_players (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    hand_id         UUID NOT NULL REFERENCES hands(id) ON DELETE CASCADE,
    seat            SMALLINT NOT NULL,
    username        VARCHAR(60) NOT NULL,
    starting_stack  BIGINT NOT NULL,
    position        VARCHAR(8) NULL,                 -- 'BTN','CO','BB',...
    is_hero         BOOLEAN NOT NULL DEFAULT false,
    sit_out         BOOLEAN NOT NULL DEFAULT false,
    posted_blind    VARCHAR(10) NULL,                -- 'sb','bb','ante','straddle' ou NULL
    blind_amount    BIGINT NOT NULL DEFAULT 0,
    hole_cards      VARCHAR(2)[] NULL,               -- só se showdown ou hero
    went_to_showdown BOOLEAN NOT NULL DEFAULT false,
    won_amount      BIGINT NOT NULL DEFAULT 0,
    final_action_street VARCHAR(10) NULL,            -- 'preflop','flop','turn','river','showdown'
    UNIQUE (hand_id, seat),
    UNIQUE (hand_id, username)
);
CREATE INDEX hand_players_hand_idx ON hand_players(hand_id);
CREATE INDEX hand_players_user_username_idx ON hand_players(username); -- útil para "vs vilão"
```

### 3.11 `actions`

Tabela mais "quente" — particionada por mês quando precisar.

```sql
CREATE TABLE actions (
    id              BIGSERIAL PRIMARY KEY,
    hand_id         UUID NOT NULL REFERENCES hands(id) ON DELETE CASCADE,
    user_id         UUID NOT NULL,                       -- desnormalizado para queries diretas
    player_id       UUID NOT NULL REFERENCES hand_players(id) ON DELETE CASCADE,
    sequence        INT NOT NULL,                        -- ordem dentro da mão
    street          VARCHAR(10) NOT NULL,                -- 'preflop'|'flop'|'turn'|'river'|'showdown'|'summary'
    action_type     VARCHAR(20) NOT NULL,                -- 'fold','check','call','bet','raise','allin','post_blind','post_ante','shows','mucks','collect','uncalled_return'
    amount          BIGINT NOT NULL DEFAULT 0,
    raise_to        BIGINT NULL,
    is_all_in       BOOLEAN NOT NULL DEFAULT false,
    pot_before      BIGINT NOT NULL DEFAULT 0,           -- pote ANTES desta ação
    pot_after       BIGINT NOT NULL DEFAULT 0,
    UNIQUE (hand_id, sequence)
);
CREATE INDEX actions_hand_idx ON actions(hand_id, sequence);
CREATE INDEX actions_user_idx ON actions(user_id);
CREATE INDEX actions_player_idx ON actions(player_id);
```

### 3.12 `pots`

Mãos com side pots requerem múltiplos potes.

```sql
CREATE TABLE pots (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    hand_id     UUID NOT NULL REFERENCES hands(id) ON DELETE CASCADE,
    pot_index   SMALLINT NOT NULL,                -- 0=main, 1=side1, ...
    amount      BIGINT NOT NULL,
    rake        BIGINT NOT NULL DEFAULT 0,
    winners     UUID[] NOT NULL,                  -- array de hand_player.id
    UNIQUE (hand_id, pot_index)
);
CREATE INDEX pots_hand_idx ON pots(hand_id);
```

### 3.13 `stats_snapshots`

Cache de estatísticas agregadas. Recalculado por Celery após cada import.

```sql
CREATE TABLE stats_snapshots (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    user_id      UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    scope_hash   CHAR(64) NOT NULL,         -- hash dos filtros (date range, stakes, position, etc.)
    scope_json   JSONB NOT NULL,
    metrics      JSONB NOT NULL,            -- { vpip: 23.4, pfr: 18.7, ... }
    sample_hands INT NOT NULL,
    computed_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, scope_hash)
);
CREATE INDEX stats_user_idx ON stats_snapshots(user_id);
```

### 3.14 `audit_logs`

Tudo que é sensível: login, deleção, mudança de plano, exportação.

```sql
CREATE TABLE audit_logs (
    id           BIGSERIAL PRIMARY KEY,
    user_id      UUID NULL REFERENCES users(id) ON DELETE SET NULL,
    actor        VARCHAR(40) NOT NULL,                  -- 'user'|'system'|'admin'
    action       VARCHAR(80) NOT NULL,                  -- 'login.success', 'data.export', 'account.delete', ...
    ip_address   INET NULL,
    user_agent   VARCHAR(255) NULL,
    metadata     JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX audit_user_time_idx ON audit_logs(user_id, created_at DESC);
CREATE INDEX audit_action_time_idx ON audit_logs(action, created_at DESC);
```

### 3.15 `feature_flags` e `feature_flag_overrides`

```sql
CREATE TABLE feature_flags (
    key         VARCHAR(80) PRIMARY KEY,
    description TEXT NULL,
    default_value JSONB NOT NULL DEFAULT 'false',
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE feature_flag_overrides (
    flag_key    VARCHAR(80) NOT NULL REFERENCES feature_flags(key) ON DELETE CASCADE,
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    value       JSONB NOT NULL,
    PRIMARY KEY (flag_key, user_id)
);
```

---

## 4. Estratégias de índice

Os índices acima cobrem queries do MVP. Regras gerais:

1. Toda FK tem índice (Postgres não cria automaticamente).
2. Toda query com `ORDER BY ... DESC LIMIT N` usa índice composto na ordem certa.
3. Índices parciais para `WHERE deleted_at IS NULL` em tabelas com soft delete.
4. Index-only scans: incluir colunas extras via `INCLUDE` quando justificar.
5. Não criar índice "por garantia" — cada índice tem custo de write. Medir com `pg_stat_statements` em staging.

---

## 5. Particionamento

- Trigger para particionar `hands` por mês quando linha count > 10M.
- Estratégia: `PARTITION BY RANGE (played_at)`, partições mensais auto-criadas via pg_partman.
- `actions` segue `hands` (mesma chave de partição).

---

## 6. Row-Level Security (RLS)

Como segunda barreira de isolamento (a primeira é a aplicação filtrar `user_id`).

```sql
ALTER TABLE hands ENABLE ROW LEVEL SECURITY;
CREATE POLICY hands_isolation ON hands
  USING (user_id = current_setting('app.user_id', true)::uuid);
```

A API seta `SET LOCAL app.user_id = '<uuid>';` no início de cada transação autenticada.

Tabelas com RLS: `users`, `imports`, `hands`, `actions`, `hand_players`, `pots`, `sessions`, `stats_snapshots`, `subscriptions`, `audit_logs`.

---

## 7. Migrations — convenções Alembic

- 1 migration = 1 mudança coesa.
- Sempre **reversível** (`downgrade()` implementado).
- Migrations destrutivas (DROP) requerem PR separado e aprovação humana.
- Para mudanças online de grande tabela: usar **`pg_repack`** ou padrão `expand → migrate dual write → contract`.

---

## 8. Seeds

`apps/api/scripts/seed.py` cria:
- 1 admin (`admin@local.test` / `admin12345!`) em ambiente local
- 3 usuários de teste com HH fixture já importado
- Feature flags com defaults

`make seed` aciona.

---

## 9. Backups e DR

- Snapshot diário do RDS, retenção 30 dias.
- WAL archive contínuo (PITR).
- Cópia semanal cross-region.
- Runbook de restore em `docs/11-DEPLOYMENT.md`.
