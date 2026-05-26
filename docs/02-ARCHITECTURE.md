# 02 — Arquitetura do sistema

> Vista de alto nível, componentes, fluxos e decisões arquiteturais (ADRs resumidas).

---

## 1. Diagrama lógico (alto nível)

```
                                    ┌─────────────────────────────────────┐
                                    │       Browser do usuário (PWA)      │
                                    │  Next.js 15 + React + TanStack      │
                                    └──────────────┬──────────────────────┘
                                                   │ HTTPS (JSON / SSE)
                                                   │
                            ┌──────────────────────▼──────────────────────┐
                            │           Edge / Reverse Proxy              │
                            │  (Cloudflare → Caddy / Nginx)               │
                            │  - TLS termination                          │
                            │  - WAF, rate limit IP                       │
                            └──────────────┬──────────────────────────────┘
                                           │
                ┌──────────────────────────┴──────────────────────────────┐
                │                                                         │
       ┌────────▼────────┐                                       ┌────────▼────────┐
       │   API (FastAPI) │   ← async, stateless, horizontal      │ Web (Next.js)   │
       │   /api/*        │                                       │  SSR / RSC      │
       └────┬────────┬───┘                                       └─────────────────┘
            │        │
            │        │ enqueue tasks
            │        ▼
            │   ┌────────────────┐
            │   │ Celery Workers │  ← parsing, stats heavy compute
            │   │ (Python)       │
            │   └──┬──────────┬──┘
            │      │          │
   ┌────────▼──────▼──┐   ┌───▼────────────┐
   │  PostgreSQL 16   │   │   Redis 7      │
   │  - hands         │   │  - cache       │
   │  - actions       │   │  - sessions    │
   │  - users         │   │  - celery brk  │
   │  - subscriptions │   │  - streams     │
   │  - billing       │   └────────────────┘
   └──────────────────┘
            │
            │
   ┌────────▼─────────┐
   │ Object Storage   │
   │ (S3 / R2)        │
   │ - HH raw files   │
   │ - exports zip    │
   └──────────────────┘

   ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
   │ Stripe webhooks  │    │ Resend (e-mail)  │    │ Sentry, OTel,    │
   │                  │    │                  │    │ Grafana Cloud    │
   └──────────────────┘    └──────────────────┘    └──────────────────┘
```

---

## 2. Componentes

### 2.1 Frontend (`apps/web`)
- **Next.js 15** com App Router, React Server Components onde aplicável.
- **TanStack Query** para estado de servidor.
- **shadcn/ui** + **Tailwind 4** para UI.
- **Recharts** para gráficos.
- **Auth.js (NextAuth v5)** para sessões; tokens armazenados em cookies `httpOnly` `Secure` `SameSite=Lax`.
- **next-intl** para i18n (PT-BR padrão).
- **PWA** com manifest + offline fallback para a rota /offline.

### 2.2 API (`apps/api`)
- **FastAPI** com routers organizados por domínio: `auth`, `users`, `hands`, `imports`, `stats`, `billing`, `admin`.
- **Pydantic v2** para schemas; cada endpoint tem `RequestModel` e `ResponseModel` explícitos.
- **SQLAlchemy 2.0 async** + **asyncpg**.
- **Alembic** para migrations.
- **Dependency Injection** estrita via `Depends`: `get_session`, `get_current_user`, `get_tenant`, `require_pro`.
- **Middleware** para: request ID, structured logging, exception handler, CORS controlado, rate limit (slowapi/limits + Redis).

### 2.3 Workers (`apps/api` mesma codebase, comando diferente)
- **Celery** com Redis como broker e backend.
- Filas separadas: `parsing` (alta CPU), `stats` (cálculos), `email` (baixa prioridade), `billing` (alta prioridade).
- Cada task é **idempotente** (chave de idempotência = hash do arquivo ou ID do evento).
- Retry policy: 3 tentativas com backoff exponencial; dead-letter para a fila `dlq`.

### 2.4 Banco de dados
- **PostgreSQL 16**, schema separado por ambiente.
- Particionamento por tempo (range) na tabela `hands` quando volume justificar (>50M linhas).
- Connection pool: pgbouncer em transaction mode.
- Backups: snapshot diário + WAL contínuo, retenção 30 dias.

### 2.5 Cache & filas
- **Redis 7**:
  - DB 0: cache de resposta da API e stats agregadas
  - DB 1: sessões (se não usar JWT puro)
  - DB 2: rate limit counters
  - DB 3: Celery broker
- TTLs:
  - cache de stats por usuário: 1h (invalidada quando importação nova)
  - cache de leaderboard / agregados públicos: 5min

### 2.6 Object Storage
- **Cloudflare R2** (zero egress, custo baixo).
- Buckets: `pi-hh-raw` (HH originais, criptografados em repouso com KMS), `pi-exports` (ZIPs de export LGPD), `pi-public-assets`.
- Pre-signed URLs com TTL curto (15min) para uploads/downloads diretos do browser.

---

## 3. Fluxos principais

### 3.1 Fluxo: Upload e parsing de HH

```
[Browser]
   │  1. POST /api/imports → recebe presigned URL
   ▼
[API] ──► gera presigned PUT URL para R2 (com chave userId/uuid)
   │      cria registro `Import` (status=pending)
   │
[Browser]
   │  2. PUT direto para R2
   ▼
[R2]
   │  3. POST /api/imports/{id}/complete
   ▼
[API] ──► enfileira `parse_import` no Celery
   │      retorna 202 com import_id
   │
[Worker - Celery]
   │  4. baixa arquivo do R2 streaming
   │  5. parser tokeniza linha a linha
   │  6. valida cada mão (schema, balanços de fichas)
   │  7. batch insert mãos+ações (1000 por trasação)
   │  8. atualiza `Import.status=succeeded` ou `failed`
   │  9. enfileira `recompute_stats(user_id)` na fila `stats`
   │
[Worker stats]
   │ 10. recalcula estatísticas agregadas
   │ 11. armazena em Postgres + invalida cache Redis
   │
[Browser]
   │ 12. SSE/polling em /api/imports/{id} mostra progresso
   ▼
   ✓ usuário vê dashboard atualizado
```

### 3.2 Fluxo: Autenticação

- Login → POST `/auth/login` com email+senha → API valida (bcrypt) → emite **access token JWT** (RS256, 15min) + **refresh token opaco** (rotacionado, armazenado em DB com `last_used_at`).
- Access token vai em cookie `httpOnly`+`Secure`+`SameSite=Lax`.
- Refresh token vai em cookie separado, com path restrito a `/auth/refresh`.
- Logout → revoga refresh; access expira sozinho.
- Detecção de uso de refresh já rotacionado → invalida toda a família (refresh rotation com reuse detection).

### 3.3 Fluxo: Cobrança Stripe

- Usuário clica "Assinar Pro" → API cria `CheckoutSession` no Stripe → redirect.
- Stripe envia webhook (`checkout.session.completed`, `invoice.paid`, `customer.subscription.deleted`) → endpoint `/webhooks/stripe`:
  - Valida assinatura HMAC do webhook (`STRIPE_WEBHOOK_SECRET`)
  - Idempotência: armazena `event.id` em tabela `webhook_events`
  - Atualiza estado em `subscriptions`
- Plano efetivo é calculado em runtime: `getUserPlan(user_id) → 'free' | 'pro'`.

---

## 4. Multi-tenancy

- Modelo: **single database, shared schema**, isolamento por `user_id` em toda query.
- Toda tabela com dado de usuário tem coluna `user_id NOT NULL` indexada.
- Camada de repositório recebe `user_id` injetado por DI; impossível chamar sem.
- Row-Level Security (RLS) do Postgres como segunda linha (com policies `current_setting('app.user_id')`).
- Testes específicos: "user A não consegue ver dado de user B" para cada endpoint protegido.

---

## 5. Concorrência e idempotência

- **Idempotency-Key** em POSTs que criam recurso (header obrigatório, armazenado por 24h).
- Imports com `file_hash` único por usuário → tentativa de re-upload é rejeitada com 409 + ID do existente.
- Webhooks Stripe: `event.id` como chave única.

---

## 6. Decisões arquiteturais (ADRs resumidas)

### ADR-001 — Monorepo com workspaces
**Decisão**: monorepo único (pnpm workspaces + Python no `apps/api`).
**Por quê**: tipos compartilhados, refactors atômicos, agentes de IA atuam num só lugar.
**Trade-off**: build mais lento sem cache; mitigado por Turborepo.

### ADR-002 — Python + FastAPI no backend
**Decisão**: Python sobre Node/Go.
**Por quê**: melhor ergonomia para parsing (regex, pandas), maturidade do ecossistema científico para futuro (range analysis, ML), familiaridade.
**Trade-off**: throughput menor que Go; mitigado por async + Celery + scaling horizontal.

### ADR-003 — PostgreSQL como única fonte da verdade
**Decisão**: nada de Mongo/Dynamo. Postgres com JSONB para campos flexíveis.
**Por quê**: ACID, joins, RLS, ferramental maduro, particionamento.
**Trade-off**: para workloads analíticos OLAP muito pesados (>500M mãos) considerar ClickHouse num data warehouse separado em V2.

### ADR-004 — JWT com refresh rotativo
**Decisão**: JWT curto + refresh rotativo armazenado no DB, ambos em cookies httpOnly.
**Por quê**: API stateless escalável; refresh permite revogação; cookies httpOnly mitigam XSS.
**Trade-off**: requer DB hit para refresh; aceitável (não é hot path).

### ADR-005 — Celery sobre RQ ou Dramatiq
**Decisão**: Celery 5 com Redis.
**Por quê**: ecossistema maduro, retries flexíveis, beat scheduler, monitoramento (Flower).
**Trade-off**: configuração mais complexa que RQ; aceitável.

### ADR-006 — Cloudflare R2 sobre AWS S3
**Decisão**: R2 para HH originais.
**Por quê**: zero egress, $0.015/GB/mês, S3-compatible API.
**Trade-off**: menos features que S3 (sem Glacier-like). Aceitável.

### ADR-007 — TypeScript estrito no front + Next.js App Router
**Decisão**: App Router (não Pages Router).
**Por quê**: RSC reduz JS no cliente, futuro do Next.
**Trade-off**: maturidade de algumas libs ainda em catch-up; aceitável em 2026.

### ADR-008 — Parser próprio em vez de port de pokerstove/pyhand
**Decisão**: parser dedicado escrito do zero, com grammar formal.
**Por quê**: parsers existentes raramente cobrem PT-BR; precisamos de testes golden próprios.
**Trade-off**: esforço inicial maior; compensado por controle total.

### ADR-009 — Plataforma de deploy: Vercel + Railway + Supabase
**Decisão**: Vercel para frontend Next.js; Railway para API FastAPI + workers Celery; Supabase para Postgres 16; Upstash para Redis.
**Por quê**: todas têm tier gratuito robusto, GitHub integration nativa (zero config de CI para deploy), e painéis web que dispensam Terraform no MVP. Vercel é plataforma já conhecida pelo time; Railway é equivalente para backend. Supabase entrega Postgres gerenciado + painel visual + backups automáticos + PITR sem overhead de ops.
**Trade-off**: menos controle granular que IaC puro; vendor lock-in parcial em features de painel. Aceitável: toda configuração crítica vive em arquivos versionados (`railway.toml`, `vercel.json`, `Dockerfile`, migrations Alembic), portabilidade garantida.
**Saída**: se necessário, migrar API para qualquer provedor Docker-compatível em <1h; DB via `pg_dump | pg_restore`; frontend em qualquer CDN que suporte Next.js.

### ADR-010 — Sem Terraform no MVP
**Decisão**: infraestrutura configurada via painéis web + arquivos de config versionados no repo.
**Por quê**: Terraform adiciona ~2 semanas de esforço de setup para 3-4 serviços que têm integração GitHub nativa. Reintroduzir quando houver múltiplos ambientes idênticos a replicar ou time de infra.

---

## 7. Ambientes

| Ambiente | Frontend | Backend | DB | Propósito |
|----------|----------|---------|-----|-----------|
| `local` | localhost:3000 | localhost:8000 | docker Postgres | desenvolvimento |
| `ci` | — | container efêmero | Postgres ephemeral | pipelines |
| `preview` | Vercel preview URL | Railway preview | Supabase staging project | PRs |
| `staging` | staging.pokerinsight.app | staging-api.pokerinsight.app | Supabase Pro | smoke tests, QA |
| `prod` | app.pokerinsight.app | api.pokerinsight.app | Supabase Pro | usuários reais |

- **Promoção**: PR → merge em `main` → deploy automático em staging (Vercel + Railway) → smoke test → tag manual `v*.*.*` → deploy prod (requer approve no GitHub Environment).
- **Feature flags** via tabela `feature_flags` (chave + json) com cache Redis 60s.

---

## 8. Diagrama de containers (dev local)

```
docker compose services:
- postgres        :5432  (db: pokerinsight)
- redis           :6379
- minio           :9000  (S3-compat para HH dev)
- mailhog         :8025  (UI), :1025 (SMTP) — captura e-mails dev
- api             :8000  (build local; volume mounted)
- worker          (Celery, conecta no redis)
- web             :3000  (Next dev server)
- jaeger          :16686 (UI traces locais)
```

---

## 9. Limites conhecidos do design

- HH em tempo real (overlay) não está coberto — entrada V2.
- Não há multi-região; latência para usuário fora do BR pode ser >100ms.
- Sem replicação read-replica no MVP; viabilizada via configuração quando o tráfego crescer.
- Não há ML model em produção; roadmap V3.
