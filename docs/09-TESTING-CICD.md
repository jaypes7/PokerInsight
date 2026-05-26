# 09 — Testes e CI/CD

> Todo PR que não passa no CI **não merga**. Sem exceções. Cobertura cai em PR → bloqueio.

## 1. Pirâmide de Testes

```
                       ┌──────────────┐
                       │  E2E (Playwr.)│   ~30 testes — fluxos críticos
                       └──────────────┘
                    ┌────────────────────┐
                    │   Integration       │   ~150 testes — API + DB real
                    └────────────────────┘
                ┌────────────────────────────┐
                │         Unit + Property     │   ~800 testes — parser, stats, libs
                └────────────────────────────┘
              ┌────────────────────────────────┐
              │      Static (mypy, ruff, eslint)│  obrigatório
              └────────────────────────────────┘
```

## 2. Backend (Python)

### 2.1 Stack
- `pytest` + `pytest-asyncio` + `pytest-cov` + `pytest-xdist` (paralelo).
- `hypothesis` para property-based.
- `freezegun` para tempo.
- `respx` (httpx mock) e `pytest-httpserver` para HTTP externo.
- `testcontainers-python` para Postgres/Redis efêmeros em integração.

### 2.2 Estrutura
```
apps/api/tests/
  unit/                # sem I/O, sem DB
    parser/
    stats/
    services/
  integration/         # com DB+Redis reais (testcontainers)
    repositories/
    api/               # FastAPI TestClient
  golden/              # fixtures HH → JSON esperado
    fixtures/
    test_golden.py
  property/            # hypothesis
  conftest.py
```

### 2.3 Categorias e regras

| Categoria | I/O permitido | Velocidade alvo | Marcador |
|---|---|---|---|
| `unit` | Nenhum | <50ms/teste | (default) |
| `integration` | Postgres+Redis (testcontainers) | <500ms/teste | `@pytest.mark.integration` |
| `golden` | Filesystem leitura | <100ms/teste | `@pytest.mark.golden` |
| `property` | Nenhum | <2s/teste | `@pytest.mark.property` |
| `slow` | Qualquer | sem limite | `@pytest.mark.slow` (não roda no CI default; nightly) |

### 2.4 Cobertura
- Global: **≥80%**.
- Código novo no PR: **≥85%**.
- Parser e stats: **≥95%** (críticos).
- Arquivos em `apps/api/app/parser/` e `apps/api/app/stats/` na lista de cobertura crítica.
- Falha do CI se cobertura cair vs `main`.

### 2.5 Golden tests
Cada fixture HH em `packages/hh-fixtures/` tem um snapshot JSON canônico em `expected/`. Mudanças no parser que alterem snapshot exigem update explícito (`pytest --update-golden`) revisado no PR.

Lista mínima de fixtures (criar todas em F1):
1. `walk_bb.txt` — todos foldam, SB completa, BB ganha sem flop.
2. `preflop_steal.txt` — open + fold geral.
3. `showdown_simple.txt` — heads-up até river com showdown.
4. `allin_uncalled.txt` — all-in que recebe uncalled bet.
5. `multiway_sidepot.txt` — 3+ jogadores, side pot.
6. `split_pot.txt` — empate, divisão.
7. `disconnect_timeout.txt` — eventos de conexão entre actions.
8. `antes_present.txt` — antes + blinds.
9. `heads_up.txt` — formato HU (BTN é SB).
10. `tournament_finish.txt` — `finished the tournament` no summary.

### 2.6 Property tests (Hypothesis)
- Parser: gerar HH sintética válida (gramática) → re-parse → invariantes.
- Stats: gerar lista de hands sintéticas → stats agregadas → invariantes (PFR ≤ VPIP, fold% ≤ 100%, etc.).
- Money: nenhuma operação produz valor negativo onde não pode.

## 3. Frontend (TS)

### 3.1 Stack
- `vitest` (unit) + `@testing-library/react`.
- `playwright` (E2E).
- `msw` para mock de API em unit.
- `storybook` opcional (v2).

### 3.2 Cobertura
- Global: **≥70%** (UI mais tolerante).
- Lib/hooks/utils: **≥85%**.

### 3.3 E2E (Playwright) — fluxos obrigatórios
1. Register → verify email (link interceptado) → login.
2. Login → upload HH → ver progresso SSE → ver hand na listagem.
3. Filtrar stats por data e position.
4. Replayer: abrir hand, navegar street a street.
5. Upgrade Free → Pro (Stripe test mode).
6. Cancel subscription via portal.
7. Export LGPD → confirmar download em email.
8. Delete account → confirmar bloqueio de login.

Rodam em `chromium` no CI; `firefox`+`webkit` no nightly.

## 4. Parser — Casos de Teste Específicos

Para cada regex em `05-HH-PARSER-SPEC.md`, ao menos 1 teste positivo e 1 negativo. Lista mínima de cenários:

- [ ] Header torneio com buy-in fracionado (`$0.42+$0.08`).
- [ ] Header cash game.
- [ ] Seats com gaps (`Lugar 1`, `Lugar 3`, `Lugar 7`).
- [ ] Username com espaço (`Arte Pokera`).
- [ ] Username com caractere especial (`José_Da_Silva-99`).
- [ ] HU summary com dupla role `(Botão)(small blind)`.
- [ ] `aumenta X para Y` com X==Y (improvável mas válido).
- [ ] `e está all-in` em call vs raise vs bet.
- [ ] Uncalled bet com valor zero (rejeitar).
- [ ] Linha de conectividade no meio de actions.
- [ ] Showdown sem mostrar cartas (`não mostrou`).
- [ ] Showdown com `Mostra a [Xx Yy]`.
- [ ] Summary `Side pot N` vs `Pote principal`.
- [ ] Hand sem flop (todos foldam).
- [ ] Hand termina no turn (sem river).
- [ ] Múltiplas hands no mesmo arquivo separadas por linhas em branco.

## 5. Integração com DB

### 5.1 Setup
- `testcontainers` sobe Postgres 16 + Redis 7 efêmeros por sessão de teste.
- Migrations aplicadas via Alembic `upgrade head` no setup.
- Transação por teste com rollback automático (fixture `db_session`).
- Cada teste cria seus dados via `factory_boy`.

### 5.2 Tenant isolation tests (obrigatório)
Para **toda** rota autenticada, teste:
1. User A loga, cria recurso X.
2. User B loga, tenta ler/editar/deletar X → **404** (não 403, para não vazar existência).

## 6. Performance Tests

- **Parser benchmark** em CI: `pytest --benchmark` rodando suíte de 10k hands sintéticas; falha se cair >20% vs baseline em `main`.
- **Query benchmark**: queries pesadas (`/v1/hands?…`, `/v1/stats`) com EXPLAIN ANALYZE em CI nightly; alerta se custo subir.
- **Load test** (semanal, k6): cenários de 100 usuários upload simultâneos; aceitação: p95 < 2s para `GET /v1/hands`.

## 7. Static Checks

| Ferramenta | Escopo | Bloqueia merge? |
|---|---|---|
| `ruff format --check` | Python | Sim |
| `ruff check` | Python | Sim |
| `mypy --strict` | Python | Sim |
| `pip-audit` | Python deps | Sim (high/critical) |
| `eslint` | TS | Sim |
| `prettier --check` | TS/MD/JSON | Sim |
| `tsc --noEmit` | TS | Sim |
| `npm audit --audit-level=high` | TS deps | Sim |
| `gitleaks` | Repo | Sim |
| `hadolint` | Dockerfile | Sim |

## 8. CI Pipeline (GitHub Actions)

### 8.1 Triggers
- `push` em qualquer branch.
- `pull_request` para `main`.
- `schedule` (cron) para nightly (load, fuzz, dep audit).

### 8.2 Jobs (paralelos onde possível)

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
  pull_request:
    branches: [main]

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  changes:
    # detecta paths alterados → pula jobs irrelevantes
    runs-on: ubuntu-latest
    outputs:
      api: ${{ steps.f.outputs.api }}
      web: ${{ steps.f.outputs.web }}
      infra: ${{ steps.f.outputs.infra }}
    steps:
      - uses: actions/checkout@v4
      - uses: dorny/paths-filter@v3
        id: f
        with:
          filters: |
            api: 'apps/api/**'
            web: 'apps/web/**'
            infra: 'infra/**'

  lint-api:
    needs: changes
    if: needs.changes.outputs.api == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: pip
      - run: pip install -r apps/api/requirements-dev.txt
      - run: cd apps/api && ruff format --check . && ruff check . && mypy --strict app

  test-api-unit:
    needs: lint-api
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12', cache: pip }
      - run: pip install -r apps/api/requirements-dev.txt
      - run: cd apps/api && pytest tests/unit tests/golden tests/property -n auto --cov=app --cov-report=xml --cov-fail-under=85
      - uses: codecov/codecov-action@v4

  test-api-integration:
    needs: lint-api
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env: { POSTGRES_PASSWORD: ci, POSTGRES_DB: ci }
        ports: ['5432:5432']
        options: --health-cmd pg_isready --health-interval 10s
      redis:
        image: redis:7
        ports: ['6379:6379']
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12', cache: pip }
      - run: pip install -r apps/api/requirements-dev.txt
      - run: cd apps/api && alembic upgrade head
        env: { DATABASE_URL: postgresql+asyncpg://postgres:ci@localhost:5432/ci }
      - run: cd apps/api && pytest tests/integration -n 4
        env:
          DATABASE_URL: postgresql+asyncpg://postgres:ci@localhost:5432/ci
          REDIS_URL: redis://localhost:6379/0

  audit-api:
    needs: changes
    if: needs.changes.outputs.api == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install pip-audit && pip-audit -r apps/api/requirements.txt --strict

  lint-web:
    needs: changes
    if: needs.changes.outputs.web == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20', cache: pnpm }
      - run: pnpm -C apps/web install --frozen-lockfile
      - run: pnpm -C apps/web lint && pnpm -C apps/web typecheck && pnpm -C apps/web format:check

  test-web:
    needs: lint-web
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20', cache: pnpm }
      - run: pnpm -C apps/web install --frozen-lockfile
      - run: pnpm -C apps/web test:coverage

  e2e:
    needs: [test-api-integration, test-web]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: docker compose -f infra/compose.ci.yml up -d
      - uses: pnpm/action-setup@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20', cache: pnpm }
      - run: pnpm -C apps/web install --frozen-lockfile
      - run: pnpm -C apps/web exec playwright install --with-deps chromium
      - run: pnpm -C apps/web e2e
      - if: failure()
        uses: actions/upload-artifact@v4
        with: { name: playwright-report, path: apps/web/playwright-report }

  gitleaks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - uses: gitleaks/gitleaks-action@v2

  build-images:
    needs: [test-api-integration, test-web, gitleaks]
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    permissions: { contents: read, packages: write }
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with: { registry: ghcr.io, username: ${{ github.actor }}, password: ${{ secrets.GITHUB_TOKEN }} }
      - uses: docker/build-push-action@v6
        with:
          context: apps/api
          push: true
          tags: ghcr.io/${{ github.repository }}/api:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
      - uses: docker/build-push-action@v6
        with:
          context: apps/web
          push: true
          tags: ghcr.io/${{ github.repository }}/web:${{ github.sha }}

  deploy-staging:
    needs: build-images
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: actions/checkout@v4
      - run: ./infra/scripts/deploy.sh staging ${{ github.sha }}
      - run: ./infra/scripts/smoke.sh https://staging.pokerinsight.app
```

### 8.3 Nightly
```yaml
on:
  schedule:
    - cron: '0 5 * * *'
jobs:
  parser-fuzz: ...
  load-test-k6: ...
  e2e-cross-browser: ...
  dep-audit-deep: ...
```

## 9. Promoção Staging → Prod

- `main` → deploy automático em **staging**.
- Tag `v*.*.*` (criada manualmente após smoke ok em staging) → deploy em **prod** via workflow `release.yml`.
- Prod precisa **aprovação manual** (`environment: production` no GitHub).
- Smoke tests pós-deploy:
  - `GET /healthz` → 200.
  - `GET /readyz` → 200.
  - `GET /version` → versão esperada.
  - Fluxo register+login com user de teste.
- Rollback: re-deploy de tag anterior (1 comando, <2min).

## 10. Definition of Done de Feature

Toda task que mexe em código precisa, antes do merge:
- [ ] Código + testes na mesma PR.
- [ ] Cobertura nova ≥ 85%.
- [ ] `ruff`, `mypy --strict`, `eslint`, `tsc` verdes.
- [ ] Sem `print`/`console.log` deixados.
- [ ] Sem `# type: ignore` ou `// @ts-ignore` sem comentário justificativo.
- [ ] Migration alembic se schema mudou (e teste de upgrade+downgrade).
- [ ] Doc atualizada se contrato público mudou.
- [ ] CHANGELOG.md atualizado (Keep a Changelog).
- [ ] PR aprovada por 1+ reviewer (humano ou agente diferente do autor).

## 11. Flakiness Policy

- Teste flaky é **bug**. Quarentena com `@pytest.mark.flaky(reruns=2)` apenas com issue aberta e prazo de 7 dias para resolver.
- Mais de 3 flakies abertos → freeze de features até resolver.
