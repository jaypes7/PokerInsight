# TODO Master — PokerInsight

> **Este é o backlog operacional.** Toda task aqui é executável por um agente de IA (Codex ou Claude Code) ou humano. Trabalhe na ordem; respeite dependências; marque o checkbox quando concluído via PR mergeado.

## Como usar este arquivo

### Para agentes de IA
1. **Sempre leia primeiro**: `README.md`, `AGENTS.md`, e os docs listados em "Docs" da task.
2. Escolha a primeira task `[ ]` (não marcada) sem dependências pendentes.
3. Confira o `Agent` sugerido: tasks marcadas `Codex` são autônomas de longa duração (parser, repositórios, migrations, testes em batch); `Claude Code` para tasks que exigem leitura ampla de contexto / discussão arquitetural / iteração rápida; `any` aceita qualquer.
4. Crie branch `<tipo>/<TASK-ID>-<slug>` (ex: `feat/F1-PARSER-003-action-line-tokenizer`).
5. Implemente. Atualize doc se contrato público mudou.
6. Abra PR seguindo template em `AGENTS.md`; inclua `Refs: <TASK-ID>` no commit/PR title.
7. Após merge, marque `[x]` aqui no mesmo PR ou em PR follow-up.

### Convenções de ID
`<FASE>-<MÓDULO>-<NN>` — ex: `F2-STATS-007`. Módulos: `INFRA`, `REPO`, `CI`, `DB`, `AUTH`, `PARSER`, `STATS`, `IMPORTS`, `HANDS`, `BILLING`, `FRONT`, `OBS`, `SEC`, `PERF`, `DEPLOY`, `DOCS`, `QA`.

### Status
- `[ ]` pendente
- `[~]` em progresso (preencher `started:` e `assignee:`)
- `[x]` concluído (preencher `merged_in:` com link de PR)
- `[!]` bloqueado (preencher `blocked_by:` e razão)

### Effort
- `XS` <2h | `S` ~半dia | `M` 1 dia | `L` 2-3 dias | `XL` ≥1 semana (quebrar antes de pegar)

---

## Fase F0 — Foundation

> Objetivo: repositório, ambiente de dev, CI verde, infraestrutura mínima para começar a codar com confiança.

### F0-REPO-001 — Inicializar monorepo
- [ ] Description: Criar repositório git público/privado, estrutura de monorepo com `pnpm` workspaces. Diretórios: `apps/api`, `apps/web`, `packages/hh-fixtures`, `packages/shared-types`, `infra/`, `docs/`, `scripts/`.
- Docs: `README.md`, `AGENTS.md`
- AC:
  - [ ] `pnpm-workspace.yaml` lista todos os pacotes.
  - [ ] `.gitignore` cobre node, python, IDE, secrets, build artifacts, `.env*`.
  - [ ] `.editorconfig`, `.gitattributes`, `LICENSE` (MIT ou Proprietary — decisão pendente, default Proprietary).
  - [ ] `CHANGELOG.md` (Keep a Changelog format) com `## [Unreleased]`.
  - [ ] README.md, AGENTS.md, e todos os `docs/*.md` versionados.
- Agent: any | Effort: S | Deps: —

### F0-REPO-002 — Conventional Commits + commit hook
- [ ] Description: Configurar `commitlint`, `husky` e `lint-staged` para forçar Conventional Commits e rodar lint local.
- Docs: `AGENTS.md`
- AC:
  - [ ] `commit-msg` hook rejeita commit fora do padrão.
  - [ ] `pre-commit` roda ruff/eslint nos arquivos staged.
  - [ ] `pre-push` roda `pnpm typecheck` e `pytest tests/unit -q` (rápido).
- Agent: Codex | Effort: S | Deps: F0-REPO-001

### F0-REPO-003 — Templates GitHub
- [ ] Description: PR template, issue templates (bug/feature/security), CODEOWNERS, FUNDING.yml (opcional), `SECURITY.md` (vulnerability disclosure), `CONTRIBUTING.md`.
- Docs: `AGENTS.md`, `08-SECURITY.md` §14
- AC:
  - [ ] `.github/PULL_REQUEST_TEMPLATE.md` com checklist da DoD.
  - [ ] `.github/ISSUE_TEMPLATE/` com 3 templates.
  - [ ] `SECURITY.md` na raiz.
  - [ ] CODEOWNERS exigindo review em `apps/api/app/auth/**`, `apps/api/app/billing/**`, `infra/**`.
- Agent: any | Effort: XS | Deps: F0-REPO-001

### F0-INFRA-001 — Docker Compose para dev
- [ ] Description: `infra/compose.dev.yml` sobe Postgres 16, Redis 7, MinIO (S3-compatible). Volumes persistentes, healthchecks, portas mapeadas. Script `make dev` sobe tudo.
- Docs: `02-ARCHITECTURE.md` §6, `03-TECH-STACK.md`
- AC:
  - [ ] `docker compose -f infra/compose.dev.yml up -d` sobe limpo.
  - [ ] DB inicializa com extensions `uuid-ossp`, `pgcrypto`, `pg_trgm`.
  - [ ] MinIO cria bucket `pokerinsight-dev` no startup (init container ou script).
  - [ ] `Makefile` targets: `dev`, `dev-down`, `dev-logs`, `dev-reset` (drop volumes).
- Agent: any | Effort: S | Deps: F0-REPO-001

### F0-INFRA-002 — Compose CI
- [ ] Description: `infra/compose.ci.yml` versão mínima usada pelos E2E em GitHub Actions.
- Docs: `09-TESTING-CICD.md` §8.2
- AC:
  - [ ] Sobe API+Web+DB+Redis+MinIO; sem volumes persistentes.
  - [ ] Imagens fixadas por SHA256.
- Agent: Codex | Effort: S | Deps: F0-INFRA-001

### F0-CI-001 — Pipeline CI base (lint + unit)
- [ ] Description: `.github/workflows/ci.yml` com jobs `changes`, `lint-api`, `lint-web`, `test-api-unit`, `test-web`.
- Docs: `09-TESTING-CICD.md` §8
- AC:
  - [ ] Concurrency cancela jobs antigos.
  - [ ] Path filter pula jobs irrelevantes.
  - [ ] Cache pip e pnpm habilitado.
  - [ ] Falha bloqueia merge em `main`.
- Agent: Codex | Effort: M | Deps: F0-REPO-001

### F0-CI-002 — Pipeline CI integração + audit
- [ ] Description: Adicionar jobs `test-api-integration`, `audit-api`, `gitleaks`.
- Docs: `09-TESTING-CICD.md` §8
- AC:
  - [ ] Job integração sobe Postgres+Redis como services.
  - [ ] `gitleaks` falha em qualquer secret detectado.
  - [ ] `pip-audit` falha em vulnerabilidades High/Critical.
- Agent: Codex | Effort: M | Deps: F0-CI-001

### F0-API-001 — Skeleton FastAPI
- [ ] Description: `apps/api/app/main.py` com FastAPI app, routers vazios, middleware de request_id, lifespan hook.
- Docs: `02-ARCHITECTURE.md`, `12-OBSERVABILITY.md` §2
- AC:
  - [ ] `uvicorn app.main:app` sobe em <2s.
  - [ ] `GET /healthz` retorna 200 com `{ "status": "ok" }`.
  - [ ] `GET /readyz` checa DB e Redis; 503 se falha.
  - [ ] `GET /version` retorna versão e SHA.
  - [ ] OpenAPI docs em `/docs` (basic auth em prod via env var).
- Agent: Codex | Effort: S | Deps: F0-INFRA-001

### F0-API-002 — Configuração via Pydantic Settings
- [ ] Description: `app/config.py` com `BaseSettings` consolidando todas as env vars; validação na startup.
- Docs: `03-TECH-STACK.md` (`.env.example`)
- AC:
  - [ ] Falha rápido se env var obrigatória ausente.
  - [ ] `.env.local` carregado em dev; ignorado em prod.
  - [ ] Tipos validados (URLs, ints, secrets).
- Agent: Codex | Effort: S | Deps: F0-API-001

### F0-API-003 — Logging estruturado
- [ ] Description: Setup `structlog` conforme `12-OBSERVABILITY.md` §2; middleware injeta `request_id`.
- Docs: `12-OBSERVABILITY.md` §2
- AC:
  - [ ] Logs em JSON em prod, console-friendly em dev.
  - [ ] Header `X-Request-ID` propagado.
  - [ ] Teste verifica que campo `request_id` aparece em log de request.
- Agent: Codex | Effort: S | Deps: F0-API-002

### F0-API-004 — SQLAlchemy 2.0 async + sessão
- [ ] Description: Engine, session factory async, dependency injection via `Depends(get_db)`. `AsyncSession` por request.
- Docs: `04-DATA-MODEL.md`
- AC:
  - [ ] Pool config conforme `10-PERFORMANCE.md` §5.
  - [ ] Encerramento de sessão limpo em erro.
  - [ ] Teste integração faz `SELECT 1`.
- Agent: Codex | Effort: S | Deps: F0-API-002

### F0-API-005 — Alembic setup
- [ ] Description: `alembic init` adaptado para async; primeira migration vazia; comando `alembic upgrade head` em CI integration.
- Docs: `04-DATA-MODEL.md` §10
- AC:
  - [ ] `alembic upgrade head` e `downgrade base` funcionam.
  - [ ] Naming convention de constraints definida.
  - [ ] Teste de migration cria DB do zero.
- Agent: Codex | Effort: S | Deps: F0-API-004

### F0-WEB-001 — Skeleton Next.js 15
- [ ] Description: `apps/web` com Next.js 15 App Router, Tailwind 4, shadcn/ui init, layout raiz, página `/` placeholder.
- Docs: `03-TECH-STACK.md`
- AC:
  - [ ] `pnpm dev` em apps/web abre `localhost:3000`.
  - [ ] Tipos TS estritos (`strict: true`).
  - [ ] ESLint + Prettier configurados; `pnpm lint` zero warnings.
- Agent: Claude Code | Effort: M | Deps: F0-REPO-001

### F0-WEB-002 — Headers de segurança
- [ ] Description: `next.config.js` define CSP, HSTS, X-Frame, Referrer-Policy conforme `08-SECURITY.md` §8.
- Docs: `08-SECURITY.md` §8
- AC:
  - [ ] Headers retornados em `/` (curl).
  - [ ] CSP não bloqueia Stripe.js.
  - [ ] Teste Playwright valida headers.
- Agent: any | Effort: S | Deps: F0-WEB-001

### F0-DOCS-001 — Publicar docs internas
- [ ] Description: Sob `/docs` no repo já está; opcionalmente publicar via MkDocs Material em `docs.pokerinsight.app` (não bloqueante).
- Docs: —
- AC:
  - [ ] `mkdocs.yml` (se optar por publicar).
  - [ ] Deploy automático em `main` push.
- Agent: any | Effort: S | Deps: F0-REPO-001 | Optional

---

## Fase F1 — Parser + Storage

> Objetivo: receber arquivo HH, validar, salvar no R2/MinIO, parsear, persistir hands no DB. Sem UI ainda.

### F1-DB-001 — Migration: users e auth tables
- [ ] Description: Migration Alembic criando `users`, `user_oauth_accounts`, `refresh_tokens`, `audit_logs`.
- Docs: `04-DATA-MODEL.md` §3.1-3.4
- AC:
  - [ ] Constraints, índices e RLS conforme spec.
  - [ ] Teste upgrade+downgrade limpo.
  - [ ] Seed de role admin via script separado (não em migration).
- Agent: Codex | Effort: M | Deps: F0-API-005

### F1-DB-002 — Migration: imports, sessions, hands, hand_players, actions, pots
- [ ] Description: Migration criando estrutura principal de dados de poker.
- Docs: `04-DATA-MODEL.md` §3.5-3.10
- AC:
  - [ ] Colunas denormalizadas em `hands` (`h_vpip`, etc.) presentes.
  - [ ] Índices essenciais criados.
  - [ ] RLS policies habilitadas.
  - [ ] Constraint `UNIQUE (user_id, site_hand_id)`.
- Agent: Codex | Effort: M | Deps: F1-DB-001

### F1-DB-003 — Migration: subscriptions, webhook_events, stats_snapshots, feature_flags
- [ ] Description: Restante do schema MVP.
- Docs: `04-DATA-MODEL.md` §3.11-3.14
- AC:
  - [ ] `webhook_events.event_id` UNIQUE.
  - [ ] `feature_flags` seed inicial (default flags off).
- Agent: Codex | Effort: S | Deps: F1-DB-002

### F1-DB-004 — Factories e fixtures de teste
- [ ] Description: `tests/factories.py` com `factory_boy` para todos os modelos. Fixture `db_session` com rollback automático.
- Docs: `09-TESTING-CICD.md` §5
- AC:
  - [ ] Criar user → linha em DB; sem leak entre testes.
  - [ ] Helper `make_hero_user()` retorna user pronto para usar.
- Agent: Codex | Effort: M | Deps: F1-DB-003

### F1-PARSER-001 — Pacote `parser` skeleton
- [ ] Description: Estrutura `app/parser/` com módulos `splitter.py`, `tokenizer.py`, `assembler.py`, `normalizer.py`, `models.py` (dataclasses `HandDraft`, `SeatDraft`, `ActionDraft`), `errors.py`.
- Docs: `05-HH-PARSER-SPEC.md` §3
- AC:
  - [ ] Tipos completos em mypy --strict.
  - [ ] Sem dependência de SQLAlchemy/web frameworks (parser puro).
- Agent: Codex | Effort: S | Deps: F0-API-001

### F1-PARSER-002 — FileSplitter (separar hands)
- [ ] Description: Função generator que recebe stream de linhas e emite chunks de linhas correspondendo a 1 hand cada (split em linha em branco após `*** SUMÁRIO ***`).
- Docs: `05-HH-PARSER-SPEC.md` §4.1
- AC:
  - [ ] Funciona com arquivo de 1 hand e de 10000 hands.
  - [ ] Tolera CRLF e LF.
  - [ ] Suporta encoding detection (utf-8-sig, cp1252).
  - [ ] Teste com fixture `tournament_finish.txt`.
- Agent: Codex | Effort: M | Deps: F1-PARSER-001

### F1-PARSER-003 — LineTokenizer (regex patterns)
- [ ] Description: Implementar todos os regex listados em `05-HH-PARSER-SPEC.md` §5. Função `tokenize(line) -> Token | None`.
- Docs: `05-HH-PARSER-SPEC.md` §5, `13-GLOSSARY.md`
- AC:
  - [ ] Cada regex em constante module-level compilada.
  - [ ] Cobertura ≥95% no módulo.
  - [ ] Teste positivo+negativo por regex (ver `09-TESTING-CICD.md` §4).
  - [ ] Token desconhecido vira `UnknownLineToken` (não exceção).
- Agent: Codex | Effort: L | Deps: F1-PARSER-001

### F1-PARSER-004 — HandAssembler (state machine)
- [ ] Description: Máquina de estados que consome tokens em ordem e popula `HandDraft` com seats, ações por street, board, summary.
- Docs: `05-HH-PARSER-SPEC.md` §4.3
- AC:
  - [ ] Erro com posição (linha+col) se transição inválida.
  - [ ] Suporta todas as fixtures golden.
  - [ ] Coverage ≥95%.
- Agent: Codex | Effort: L | Deps: F1-PARSER-003

### F1-PARSER-005 — HandNormalizer (derivações)
- [ ] Description: Pós-processamento: converter played_at ET→UTC; derivar posições (BTN/SB/BB/UTG/etc.); calcular `pot_before/after` por action; identificar uncalled bet; calcular side pots; popular flags hero (`h_vpip`, `h_pfr`, etc.).
- Docs: `05-HH-PARSER-SPEC.md` §4.4, `06-POKER-STATS-SPEC.md`
- AC:
  - [ ] Algoritmo de side pots passa em fixture `multiway_sidepot.txt`.
  - [ ] Posições corretas em 9-max, 6-max, HU (verificar com fixtures).
  - [ ] `h_vpip` e `h_pfr` calculados conforme spec stats.
  - [ ] Coverage ≥95%.
- Agent: Codex | Effort: L | Deps: F1-PARSER-004

### F1-PARSER-006 — Validação de invariantes
- [ ] Description: Função `validate(draft: HandDraft) -> list[Invariant Violation]`. Implementa 10 invariantes listados em `05-HH-PARSER-SPEC.md`.
- Docs: `05-HH-PARSER-SPEC.md` §7
- AC:
  - [ ] Cada invariante tem teste positivo (passa) e negativo (detecta).
  - [ ] Violação grava em `import_errors` mas não aborta o batch.
- Agent: Codex | Effort: M | Deps: F1-PARSER-005

### F1-PARSER-007 — Golden fixtures + tests
- [ ] Description: Criar 10 fixtures `.txt` listadas em `09-TESTING-CICD.md` §2.5 e seus snapshots JSON esperados em `expected/`. Teste roda parser e compara.
- Docs: `09-TESTING-CICD.md` §2.5
- AC:
  - [ ] 10 fixtures anonimizadas (sem nicks reais) committed.
  - [ ] CLI `pytest --update-golden` regenera snapshots.
  - [ ] Snapshot tem todos campos relevantes (não apenas pot_total).
- Agent: Codex | Effort: L | Deps: F1-PARSER-005

### F1-PARSER-008 — Property tests (Hypothesis)
- [ ] Description: Generators que produzem HHs sintéticas válidas; parser+invariantes nunca falham nelas.
- Docs: `09-TESTING-CICD.md` §2.6
- AC:
  - [ ] ≥3 properties: round-trip render/parse, invariantes sempre OK, posições derivadas consistentes.
  - [ ] Suite roda em <60s.
- Agent: Codex | Effort: M | Deps: F1-PARSER-006

### F1-PARSER-009 — Anonymizer CLI
- [ ] Description: Script `scripts/anonymize_hh.py` que recebe HH e troca usernames por `Player1..PlayerN`, valores por estilizados se necessário.
- Docs: `05-HH-PARSER-SPEC.md` §10
- AC:
  - [ ] Determinístico (mesma entrada → mesma saída).
  - [ ] Mantém hero (configurável) ou anonimiza tudo.
  - [ ] Teste verifica que parser ainda processa o output.
- Agent: any | Effort: S | Deps: F1-PARSER-002

### F1-PARSER-010 — Parser benchmark
- [ ] Description: Suite `pytest-benchmark` rodando parser em fixture de 10k hands sintéticas; falha se cair >20% vs baseline.
- Docs: `10-PERFORMANCE.md` §7.5
- AC:
  - [ ] Throughput ≥1000 hands/s em CI runner padrão.
  - [ ] Baseline checkado em `tests/benchmarks/baseline.json`.
- Agent: Codex | Effort: S | Deps: F1-PARSER-008

### F1-REPO-001 — Repositórios (Hands, Imports, Sessions)
- [ ] Description: Camada de acesso a dados com classes `HandsRepository`, `ImportsRepository`, `SessionsRepository`. Todas as queries com `user_id` explícito.
- Docs: `10-PERFORMANCE.md` §2
- AC:
  - [ ] Bulk insert `insert_many(drafts)` com chunks de 1000.
  - [ ] Sem N+1 (verificar com `query_count` fixture).
  - [ ] Coverage ≥90%.
- Agent: Codex | Effort: M | Deps: F1-DB-002, F1-PARSER-005

### F1-STORAGE-001 — Cliente R2/S3 + presigned URLs
- [ ] Description: Wrapper sobre `boto3` (ou `aioboto3`) configurado para R2 em prod e MinIO em dev. Métodos `generate_presigned_put`, `generate_presigned_get`, `get_object`.
- Docs: `02-ARCHITECTURE.md`, `08-SECURITY.md` §5
- AC:
  - [ ] TTL de presigned PUT ≤15min.
  - [ ] Path enforcement `users/{user_id}/imports/{import_id}.txt`.
  - [ ] Teste com MinIO valida fluxo.
- Agent: Codex | Effort: M | Deps: F0-INFRA-001

### F1-WORKER-001 — Celery setup
- [ ] Description: `app/worker/celery_app.py` com 4 queues (`parsing`, `stats`, `email`, `billing`); worker startup script; Redis como broker.
- Docs: `02-ARCHITECTURE.md`, `03-TECH-STACK.md`
- AC:
  - [ ] `celery -A app.worker.celery_app worker -Q parsing` sobe.
  - [ ] OTel instrumentation Celery habilitada.
  - [ ] Tasks com retry + backoff exponencial.
- Agent: Codex | Effort: M | Deps: F0-API-002

### F1-WORKER-002 — Task: process_import
- [ ] Description: Task Celery que pega `import_id`, baixa do R2, splita+parsea, persiste hands em batch, atualiza `imports.status`, emite eventos SSE (via Redis pub/sub).
- Docs: `02-ARCHITECTURE.md` §4.1
- AC:
  - [ ] Idempotente (reprocessar mesmo import dá mesmo resultado).
  - [ ] Progress reportado a cada 500 hands.
  - [ ] Erros agregados em `import_errors`; status final `processed` ou `failed`.
- Agent: Codex | Effort: L | Deps: F1-REPO-001, F1-STORAGE-001, F1-WORKER-001

### F1-API-001 — Auth: register + login + logout
- [ ] Description: Endpoints `POST /v1/auth/register`, `POST /v1/auth/login`, `POST /v1/auth/logout`. Argon2id, validação de senha contra HIBP, rate limit, cookies httpOnly.
- Docs: `07-API-SPEC.md` §3, `08-SECURITY.md` §2
- AC:
  - [ ] Email confirmação enviado em register (com Resend, mock em test).
  - [ ] Senhas hasheadas com Argon2id.
  - [ ] Rate limit testado.
  - [ ] Tenant isolation tests para qualquer endpoint que crie dado.
- Agent: Codex | Effort: L | Deps: F1-DB-001

### F1-API-002 — Auth: refresh + verify email + password reset
- [ ] Description: Endpoints `POST /v1/auth/refresh` (rotação + reuse detection), `POST /v1/auth/verify-email`, `POST /v1/auth/forgot-password`, `POST /v1/auth/reset-password`.
- Docs: `07-API-SPEC.md` §3.3-3.5, `08-SECURITY.md` §2.3-2.5
- AC:
  - [ ] Reuse de refresh detectado → revoga família + log.
  - [ ] Token de reset single-use + TTL 30min.
- Agent: Codex | Effort: L | Deps: F1-API-001

### F1-API-003 — Imports endpoints
- [ ] Description: `POST /v1/imports` (gera presigned URL), `POST /v1/imports/{id}/complete` (enfileira task), `GET /v1/imports` (listar), `GET /v1/imports/{id}` (status), `GET /v1/imports/{id}/events` (SSE progress).
- Docs: `07-API-SPEC.md` §5
- AC:
  - [ ] SSE envia eventos `progress`, `error`, `done`.
  - [ ] Quota diária respeitada (Free 200MB, Pro 2GB).
  - [ ] Idempotency-Key suportado em POST.
- Agent: Codex | Effort: L | Deps: F1-STORAGE-001, F1-WORKER-002

### F1-API-004 — Hands endpoints
- [ ] Description: `GET /v1/hands` (lista com filtros + cursor pagination), `GET /v1/hands/{id}` (detail com seats+actions+pots), `GET /v1/hands/{id}/raw` (texto original).
- Docs: `07-API-SPEC.md` §6, `10-PERFORMANCE.md` §2.5
- AC:
  - [ ] Filtros: date_from/to, game_type, buyin_min/max, position, went_to_showdown.
  - [ ] EXPLAIN ANALYZE no PR.
  - [ ] Sem N+1 (teste).
  - [ ] Tenant isolation test.
- Agent: Codex | Effort: L | Deps: F1-REPO-001, F1-API-002

### F1-QA-001 — E2E: upload → parse → list
- [ ] Description: Teste Playwright que faz register → login → upload de fixture → aguarda processed → ver hand na listagem.
- Docs: `09-TESTING-CICD.md` §3.3
- AC:
  - [ ] Roda em <60s em CI.
  - [ ] Email mock (link de verificação interceptado).
- Agent: Claude Code | Effort: M | Deps: F1-API-003, F1-API-004

---

## Fase F2 — Stats Core

> Objetivo: calcular as 7 métricas MVP do spec, expor via API, ter testes determinísticos.

### F2-STATS-001 — Módulo `stats/` skeleton
- [ ] Description: `app/stats/` com módulos por métrica; cada uma com função `compute_from_hands(hands_query)` retornando `MetricResult`.
- Docs: `06-POKER-STATS-SPEC.md`
- AC:
  - [ ] Tipos completos.
  - [ ] Doc string com fórmula exata.
- Agent: Codex | Effort: S | Deps: F1-PARSER-005

### F2-STATS-002 — VPIP, PFR
- [ ] Description: Implementar VPIP e PFR usando colunas denormalizadas `h_vpip`, `h_pfr` agregadas via SQL.
- Docs: `06-POKER-STATS-SPEC.md` §3.1-3.2
- AC:
  - [ ] Walk-in-BB convention respeitada (verificar com fixture `walk_bb.txt`).
  - [ ] Invariante PFR ≤ VPIP em todo teste.
  - [ ] Coverage ≥95%.
- Agent: Codex | Effort: M | Deps: F2-STATS-001

### F2-STATS-003 — 3-Bet% e Fold to 3-Bet%
- [ ] Description: Implementar 3-Bet% (oportunidade = enfrentou open, ainda não agiu) e Fold to 3-Bet% (denominador = open + foi 3-betado).
- Docs: `06-POKER-STATS-SPEC.md` §3.3-3.4
- AC:
  - [ ] Fixtures dedicadas no test (heads-up open + 3-bet, multiway sem oportunidade).
  - [ ] Coverage ≥95%.
- Agent: Codex | Effort: M | Deps: F2-STATS-002

### F2-STATS-004 — AF (Aggression Factor)
- [ ] Description: AF postflop = (bets+raises)/calls. Tratamento para calls=0.
- Docs: `06-POKER-STATS-SPEC.md` §3.5
- AC:
  - [ ] Caso calls=0 retorna `null` ou marcador (decisão em spec).
  - [ ] Teste com fixture showdown_simple.
- Agent: Codex | Effort: S | Deps: F2-STATS-002

### F2-STATS-005 — WTSD% e W$SD%
- [ ] Description: WTSD = went_to_showdown / saw_flop. W$SD = won_at_showdown / went_to_showdown.
- Docs: `06-POKER-STATS-SPEC.md` §3.6-3.7
- AC:
  - [ ] Hand chopada (split pot) conta como won? Documentar e testar.
- Agent: Codex | Effort: M | Deps: F2-STATS-002

### F2-STATS-006 — Filtros agregadores
- [ ] Description: Função `compute_stats(user_id, filters)` que aplica `date_from/to`, `game_type`, `buyin_range`, `position` antes de agregar.
- Docs: `06-POKER-STATS-SPEC.md` §5
- AC:
  - [ ] Mesmo filtro aplicado em todas as 7 stats.
  - [ ] EXPLAIN ANALYZE em PR.
  - [ ] Cobertura ≥90%.
- Agent: Codex | Effort: M | Deps: F2-STATS-005

### F2-STATS-007 — Breakdown por posição
- [ ] Description: Retornar stats agrupadas por posição (BTN/SB/BB/UTG/MP/CO/etc).
- Docs: `06-POKER-STATS-SPEC.md` §5
- AC:
  - [ ] SQL único agregando GROUP BY position.
  - [ ] Posição `null` (sem dado) excluída.
- Agent: Codex | Effort: S | Deps: F2-STATS-006

### F2-STATS-008 — Cache Redis para stats
- [ ] Description: Wrap `compute_stats` com cache; chave inclui hash dos filtros e `user_id`; TTL 1h.
- Docs: `10-PERFORMANCE.md` §6
- AC:
  - [ ] Invalidação ao `import.completed` (worker emite evento).
  - [ ] Stampede protection via lock.
  - [ ] Teste verifica hit/miss.
- Agent: Codex | Effort: M | Deps: F2-STATS-006

### F2-API-001 — Endpoint `GET /v1/stats`
- [ ] Description: Endpoint que retorna stats + breakdown por posição usando query params para filtros.
- Docs: `07-API-SPEC.md` §7
- AC:
  - [ ] Documentado em OpenAPI.
  - [ ] Validação Pydantic dos filtros.
  - [ ] Warning de "sample baixo" se hands<500.
  - [ ] Tenant isolation test.
- Agent: Codex | Effort: S | Deps: F2-STATS-008

### F2-API-002 — Endpoint `GET /v1/stats/bankroll`
- [ ] Description: Série temporal de buy-ins e prêmios em torneios para gráfico.
- Docs: `07-API-SPEC.md` §7
- AC:
  - [ ] Agrupamento por dia/semana/mês via param.
  - [ ] Retorna `{ts, cumulative_pnl_cents, hands_played}` por bucket.
- Agent: Codex | Effort: M | Deps: F1-API-004

### F2-WORKER-001 — Task: rebuild_stats_snapshot
- [ ] Description: Task noturna que materializa `stats_snapshots` por user para acelerar dashboards.
- Docs: `10-PERFORMANCE.md` §6.1
- AC:
  - [ ] Roda em <10min para 10k users.
  - [ ] Scheduled via Celery beat.
- Agent: Codex | Effort: M | Deps: F2-STATS-006

---

## Fase F3 — Frontend MVP

> Objetivo: tela utilizável para o usuário fazer upload, ver hands, ver stats.

### F3-FRONT-001 — Auth client (login, register, refresh)
- [ ] Description: Hooks `useLogin`, `useRegister`, `useLogout`, `useSession`; refresh automático via interceptor; redirect para `/login` se 401.
- Docs: `07-API-SPEC.md` §3
- AC:
  - [ ] Cookies httpOnly, sem token em JS.
  - [ ] CSRF token enviado em mutations.
- Agent: Claude Code | Effort: L | Deps: F0-WEB-001, F1-API-002

### F3-FRONT-002 — Páginas: landing, login, register, forgot/reset
- [ ] Description: Páginas com forms, validação, UI shadcn, PT-BR.
- Docs: —
- AC:
  - [ ] Acessível (a11y básica, axe sem erros sérios).
  - [ ] Mobile-responsive.
- Agent: Claude Code | Effort: L | Deps: F3-FRONT-001

### F3-FRONT-003 — Layout autenticado + navegação
- [ ] Description: Sidebar/topbar com links: Dashboard, Upload, Hands, Stats, Configurações, Billing.
- Docs: —
- AC:
  - [ ] Active link destacado.
  - [ ] User menu com email + logout.
- Agent: Claude Code | Effort: M | Deps: F3-FRONT-002

### F3-FRONT-004 — Upload page com SSE progress
- [ ] Description: Drag & drop, lista de uploads recentes com progresso ao vivo (SSE).
- Docs: `07-API-SPEC.md` §5
- AC:
  - [ ] Aborta upload em erro client-side de tamanho.
  - [ ] Mostra erros do parser por hand (de `import_errors`).
- Agent: Claude Code | Effort: L | Deps: F1-API-003, F3-FRONT-003

### F3-FRONT-005 — Hands listing (virtualizada)
- [ ] Description: Tabela infinite-scroll com filtros (date range, position, game type, etc.).
- Docs: `07-API-SPEC.md` §6
- AC:
  - [ ] Virtualized (TanStack Virtual) para 10k+ linhas.
  - [ ] Filtros sincronizados com URL.
- Agent: Claude Code | Effort: L | Deps: F1-API-004, F3-FRONT-003

### F3-FRONT-006 — Hand detail + replayer
- [ ] Description: Página que mostra hand street-by-street com cartas, board, ações, e botões prev/next. Componente reusável `<HandReplayer />`.
- Docs: —
- AC:
  - [ ] Lazy-loaded (`next/dynamic`).
  - [ ] Mostra raw text expandable.
  - [ ] Renderiza side pots se houver.
- Agent: Claude Code | Effort: XL | Deps: F1-API-004

### F3-FRONT-007 — Stats dashboard
- [ ] Description: Cards com VPIP, PFR, 3B, F3B, AF, WTSD, W$SD + breakdown por posição (chart). Filtros idem hands.
- Docs: `07-API-SPEC.md` §7
- AC:
  - [ ] Loading skeleton.
  - [ ] Tooltip com fórmula em cada métrica.
  - [ ] Warning "amostra baixa" se hands<500.
- Agent: Claude Code | Effort: L | Deps: F2-API-001, F3-FRONT-003

### F3-FRONT-008 — Bankroll chart
- [ ] Description: Gráfico de linha com PnL cumulativo de torneios (recharts).
- Docs: `07-API-SPEC.md` §7
- AC:
  - [ ] Toggle dia/semana/mês.
  - [ ] Tooltip por ponto.
- Agent: Claude Code | Effort: M | Deps: F2-API-002

### F3-FRONT-009 — Settings page
- [ ] Description: Trocar senha, atualizar email, idioma (PT-BR/EN-v2), timezone, deletar conta, exportar dados (LGPD).
- Docs: `07-API-SPEC.md` §4, `08-SECURITY.md` §11.2
- AC:
  - [ ] Delete account requer confirmação por senha e typing "DELETAR".
  - [ ] Export gera download via email após processamento.
- Agent: Claude Code | Effort: M | Deps: F1-API-002

### F3-QA-001 — E2E completos da fase F3
- [ ] Description: Implementar todos os fluxos E2E listados em `09-TESTING-CICD.md` §3.3 (exceto billing).
- Docs: `09-TESTING-CICD.md` §3.3
- AC:
  - [ ] 7 cenários verdes em CI.
  - [ ] Tempo total <10min.
- Agent: Claude Code | Effort: L | Deps: F3-FRONT-009

---

## Fase F4 — Billing + Limits

> Objetivo: Stripe ativo, plano Pro, limites do free aplicados, portal funcionando.

### F4-BILLING-001 — Stripe setup
- [ ] Description: Criar products/prices no painel Stripe (test mode); configurar webhook endpoint; adicionar secrets no Railway.
- Docs: `11-DEPLOYMENT.md` §6
- AC:
  - [ ] Product "Plano Pro" com preço mensal e anual criados.
  - [ ] Webhook registrado para `main` e `prod` URLs.
  - [ ] Secrets `STRIPE_SECRET_KEY` e `STRIPE_WEBHOOK_SECRET` no Railway.
- Agent: any | Effort: M | Deps: —

### F4-BILLING-002 — Customer + Checkout session
- [ ] Description: Endpoints `POST /v1/billing/checkout` cria session; redirect; criar `stripe_customer_id` no user.
- Docs: `07-API-SPEC.md` §8
- AC:
  - [ ] Idempotência via Idempotency-Key.
  - [ ] Teste com Stripe test mode.
- Agent: Codex | Effort: M | Deps: F4-BILLING-001, F1-API-002

### F4-BILLING-003 — Webhook handler idempotente
- [ ] Description: `POST /v1/billing/webhook/stripe` valida assinatura, salva em `webhook_events` (UNIQUE event_id), processa: subscription.created/updated/deleted, invoice.paid/failed.
- Docs: `02-ARCHITECTURE.md` §4.3, `07-API-SPEC.md` §8
- AC:
  - [ ] Assinatura verificada com tolerância 5min.
  - [ ] Reprocesso de event_id duplicado é no-op.
  - [ ] Atualiza `subscriptions` table.
- Agent: Codex | Effort: L | Deps: F4-BILLING-002

### F4-BILLING-004 — Portal session
- [ ] Description: `POST /v1/billing/portal` retorna URL do portal Stripe pré-autenticada.
- Docs: `07-API-SPEC.md` §8
- AC:
  - [ ] Funciona com customer existente.
  - [ ] Erro claro se usuário não tem subscription.
- Agent: Codex | Effort: S | Deps: F4-BILLING-002

### F4-BILLING-005 — Limites de plano (middleware)
- [ ] Description: Middleware que checa quotas (hands/mês, upload/dia) antes de aceitar import; usa `subscription.plan`.
- Docs: `01-PRD.md`, `08-SECURITY.md` §6
- AC:
  - [ ] Free: 5k hands/30d, 200MB upload/dia.
  - [ ] Pro: 200k hands/30d (soft), 2GB/dia.
  - [ ] Resposta 402 Payment Required quando excede.
- Agent: Codex | Effort: M | Deps: F4-BILLING-003

### F4-FRONT-001 — Billing pages
- [ ] Description: Página de planos, upgrade button → checkout; página "Minha assinatura" com plano atual e link para portal.
- Docs: `07-API-SPEC.md` §8
- AC:
  - [ ] CSP permite Stripe.js.
  - [ ] Cancelamento testado em test mode.
- Agent: Claude Code | Effort: M | Deps: F4-BILLING-004, F3-FRONT-003

### F4-QA-001 — E2E billing
- [ ] Description: Cenários 5 e 6 de `09-TESTING-CICD.md` §3.3 implementados.
- Docs: `09-TESTING-CICD.md` §3.3
- AC:
  - [ ] Upgrade funciona em Stripe test mode.
  - [ ] Cancelamento funciona.
- Agent: Claude Code | Effort: M | Deps: F4-FRONT-001

---

## Fase F5 — Polish + Launch

> Objetivo: observabilidade prod, hardening, performance, lançamento beta closed.

### F5-OBS-001 — OpenTelemetry traces + metrics
- [ ] Description: Setup OTel SDK; exporter OTLP → Grafana Cloud; instrumentação automática FastAPI/SQLA/Redis/Celery.
- Docs: `12-OBSERVABILITY.md` §3-4
- AC:
  - [ ] Traces visíveis no Tempo.
  - [ ] Métricas RED por endpoint no Grafana.
  - [ ] Sample rate configurável por env.
- Agent: Codex | Effort: M | Deps: F0-API-003

### F5-OBS-002 — Sentry backend + frontend
- [ ] Description: SDK em ambos; release tagging por SHA; source maps frontend; redaction de PII.
- Docs: `12-OBSERVABILITY.md` §5
- AC:
  - [ ] Exception forçada aparece no projeto correto.
  - [ ] PII redactada (verificar com teste).
- Agent: any | Effort: S | Deps: F0-API-003, F0-WEB-001

### F5-OBS-003 — Dashboards Grafana
- [ ] Description: Dashboards JSON versionados conforme `12-OBSERVABILITY.md` §6.
- Docs: `12-OBSERVABILITY.md` §6
- AC:
  - [ ] 4 dashboards (Overview, Parser, Business, Infra).
  - [ ] Variáveis env/service funcionam.
- Agent: any | Effort: M | Deps: F5-OBS-001

### F5-OBS-004 — Alertas
- [ ] Description: Configurar regras de alerta conforme tabela em `12-OBSERVABILITY.md` §7. Slack webhooks; PagerDuty opcional para critical.
- Docs: `12-OBSERVABILITY.md` §7
- AC:
  - [ ] Cada alerta tem runbook linkado.
  - [ ] Teste de fogo (dispara manualmente) funciona.
- Agent: any | Effort: M | Deps: F5-OBS-003

### F5-SEC-001 — Audit hardening
- [ ] Description: Revisão final de:
  - Headers (verificar via Mozilla Observatory).
  - Rate limits ativos em todos os endpoints sensíveis.
  - Audit log em todas as ações listadas.
  - Tenant isolation tests cobrem todos os endpoints autenticados.
- Docs: `08-SECURITY.md`
- AC:
  - [ ] Mozilla Observatory A+.
  - [ ] Checklist `08-SECURITY.md` §15 passado em PR review.
- Agent: any | Effort: M | Deps: —

### F5-SEC-002 — Penetration test interno
- [ ] Description: Rodar OWASP ZAP baseline + manual review de endpoints sensíveis. Documentar findings.
- Docs: `08-SECURITY.md`
- AC:
  - [ ] Sem findings High/Critical.
  - [ ] Mediums com plano de mitigação documentado.
- Agent: any | Effort: M | Deps: F5-SEC-001

### F5-PERF-001 — Load test k6
- [ ] Description: Script k6 simulando 100 usuários concorrentes uploads + listing + stats.
- Docs: `10-PERFORMANCE.md` §1
- AC:
  - [ ] Budgets de `10-PERFORMANCE.md` §1 respeitados.
  - [ ] Relatório commitado em `docs/perf-reports/`.
- Agent: Codex | Effort: M | Deps: F3-FRONT-007

### F5-PERF-002 — Query review
- [ ] Description: `pg_stat_statements` analisado; top 20 queries com EXPLAIN ANALYZE documentado; índices criados se necessário.
- Docs: `10-PERFORMANCE.md` §10
- AC:
  - [ ] Nenhuma query top 20 com seq scan em tabela >100k linhas.
  - [ ] Documento `docs/perf-reports/query-review-{date}.md`.
- Agent: Codex | Effort: M | Deps: F5-PERF-001

### F5-LGPD-001 — Páginas legais
- [ ] Description: `/privacidade`, `/termos`, `/sub-processadores`, `/.well-known/security.txt` em PT-BR; revisão por advogado externo recomendada.
- Docs: `08-SECURITY.md` §11
- AC:
  - [ ] Conteúdo cobre §11 de SECURITY.
  - [ ] Cookie banner em PT-BR funcional.
- Agent: any | Effort: M | Deps: —

### F5-LGPD-002 — Export + Delete flow E2E
- [ ] Description: Validar end-to-end o fluxo de export (gera ZIP, manda email com link expirante) e delete (soft + hard em 30d via task).
- Docs: `08-SECURITY.md` §11.2
- AC:
  - [ ] Teste E2E no CI.
  - [ ] HH files removidos do R2 após hard delete.
- Agent: Codex | Effort: L | Deps: F3-FRONT-009

### F5-DEPLOY-001 — Setup inicial das plataformas (você faz uma vez)
- [ ] Description: Criar contas e conectar os serviços conforme `11-DEPLOYMENT.md` §4. Os agentes geram os arquivos de config; você faz login e cola as variáveis de ambiente.
- Docs: `11-DEPLOYMENT.md` §4, §5, §6
- AC:
  - [ ] Conta Vercel conectada ao GitHub repo; frontend faz deploy ao push em `main`.
  - [ ] Projeto Railway criado com 2 services (api + worker); deploy ao push em `main`.
  - [ ] Projeto Supabase criado; `DATABASE_URL` adicionada ao Railway.
  - [ ] Database Upstash criado; `REDIS_URL` adicionada ao Railway.
  - [ ] Bucket R2 criado; credenciais no Railway.
  - [ ] Todas as variáveis em `11-DEPLOYMENT.md` §6 preenchidas.
  - [ ] `railway.toml` e `vercel.json` commitados no repo.
  - [ ] Domínios `app.pokerinsight.app` e `api.pokerinsight.app` configurados via DNS Cloudflare.
- Agent: **você** (requer login) + agentes geram arquivos | Effort: M | Deps: F0-CI-002

### F5-DEPLOY-002 — Primeiro deploy em produção
- [ ] Description: Criar tag `v0.1.0`; workflow `release.yml` pede aprovação manual no GitHub; deploy vai para Vercel prod + Railway prod; migrations rodam via `releaseCommand` no Railway.
- Docs: `11-DEPLOYMENT.md` §7
- AC:
  - [ ] `https://app.pokerinsight.app` carrega.
  - [ ] `https://api.pokerinsight.app/healthz` retorna 200.
  - [ ] `GET /version` retorna o SHA correto.
  - [ ] Smoke tests do workflow verdes.
- Agent: any | Effort: M | Deps: F5-DEPLOY-001, F5-OBS-004

### F5-DEPLOY-003 — Disaster recovery drill
- [ ] Description: Simular perda do DB e restaurar via PITR; cronometrar; documentar RTO real.
- Docs: `11-DEPLOYMENT.md` §6.1, §12
- AC:
  - [ ] RTO ≤1h alcançado.
  - [ ] Runbook ajustado com aprendizados.
- Agent: any | Effort: M | Deps: F5-DEPLOY-002

### F5-LAUNCH-001 — Beta closed (invites)
- [ ] Description: 30-50 usuários beta com feedback channel (Discord/Slack); coletar bugs e melhorias por 2 semanas antes de open beta.
- Docs: `01-PRD.md`
- AC:
  - [ ] Form de inscrição na landing.
  - [ ] Métricas de NSM monitoradas.
- Agent: any | Effort: M | Deps: F5-DEPLOY-002

### F5-LAUNCH-002 — Documentação pública (user docs)
- [ ] Description: Site `help.pokerinsight.app` ou seção `/ajuda` com guias: "Como exportar HH do PokerStars", "Entendendo as stats", "FAQ", "Sobre a privacidade".
- Docs: `13-GLOSSARY.md`
- AC:
  - [ ] 10+ artigos em PT-BR.
  - [ ] Searchable.
- Agent: any | Effort: L | Deps: —

### F5-LAUNCH-003 — Launch checklist (gate)
- [ ] Description: Checklist final antes de open beta. Inclui:
  - [ ] Todos os SLOs configurados.
  - [ ] Backups testados.
  - [ ] Suporte ao usuário com canal definido.
  - [ ] Stripe live mode validado em prod.
  - [ ] Status page operacional.
  - [ ] LGPD: DPO contactable, RoPA preenchido.
  - [ ] Páginas legais revisadas.
  - [ ] CHANGELOG atualizado.
  - [ ] Release notes do `v1.0.0` publicadas.
- Agent: any | Effort: S | Deps: ALL ABOVE

---

## Backlog (pós-MVP)

Tarefas identificadas mas fora do MVP. Não bloqueiam launch.

- C-Bet%, 4-Bet%, Squeeze%, Steal%, Probe%, Donk%, Float, ChR, WWSF.
- Suporte a outros sites (GGPoker, PartyPoker, WPN).
- Spin & Go support.
- PLO support.
- Range visualizer.
- Hand replayer com export para PNG/MP4.
- Notas e tags por villain.
- HUD em tempo real (requer client desktop — out of scope).
- App mobile (React Native).
- Stripe Pix (já habilitado por padrão em BR; testar fluxo).
- 2FA (TOTP).
- API pública para coaches integrarem com seus alunos.
- Equity calculator integrado.
- Leak finder (heurísticas sobre padrões).
- Sessões: detecção automática (vs upload manual).

---

## Atalhos para AI Agents

### "Estou começando do zero, qual a primeira task?"
→ **F0-REPO-001**.

### "Estou implementando o parser, por onde começo?"
→ Verificar F0 e F1-DB-001..004 prontos. Depois F1-PARSER-001 → 002 → 003 → 004 → 005 em ordem.

### "Como adicionar uma nova stat (v2)?"
→ Adicionar coluna denormalizada em `hands` via migration → atualizar parser para popular → adicionar módulo em `app/stats/` → expor em `/v1/stats` (campo opcional) → atualizar `06-POKER-STATS-SPEC.md`.

### "Como adicionar suporte a outro site (ex: GGPoker)?"
→ Criar `app/parser/sites/ggpoker/` espelhando estrutura PokerStars. Adicionar `site` enum em `hands`. Detectar site no FileSplitter. Criar fixtures golden.

### "PR foi reprovado em coverage, e agora?"
→ Não pegue a próxima task. Volte na atual, adicione testes para o código não coberto. Se a cobertura cair em código não tocado, problema é flakiness — investigue.
