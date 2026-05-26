# 03 — Tech Stack & versões fixadas

> Este é o **contrato técnico** do projeto. Mudança de versão major requer ADR (registrar em `02-ARCHITECTURE.md`).

---

## 1. Versões fixadas

### Linguagens e runtimes

| Item | Versão | Notas |
|------|--------|-------|
| Python | **3.12.x** (último patch) | pinned no `.python-version` |
| Node.js | **20.x LTS** | pinned no `.nvmrc` |
| pnpm | **9.x** | em `package.json` engines |
| PostgreSQL via **Supabase** | **16.x** | DB gerenciado (free tier → Pro $25/mês) |
| Redis via **Upstash** | **7.x** | serverless Redis (free → pay-per-use) |
| Docker | qualquer recente | engine + compose v2 |
| uv (Python) | last stable | substitui pip+pip-tools |

### Backend (Python)

| Pacote | Versão (min) | Função |
|--------|--------------|--------|
| fastapi | ^0.115 | Web framework |
| uvicorn[standard] | ^0.30 | ASGI server |
| pydantic | ^2.8 | Schemas |
| pydantic-settings | ^2.4 | Config via env |
| sqlalchemy[asyncio] | ^2.0 | ORM async |
| asyncpg | ^0.29 | Postgres driver |
| alembic | ^1.13 | Migrations |
| celery[redis] | ^5.4 | Filas |
| flower | ^2.0 | UI Celery (dev/staging) |
| redis | ^5.0 | Cliente |
| boto3 | ^1.35 | S3/R2 client |
| python-jose[cryptography] | ^3.3 | JWT |
| passlib[bcrypt] | ^1.7 | Hash de senha (usar argon2id também) |
| argon2-cffi | ^23 | Hash de senha preferido |
| structlog | ^24 | Logs estruturados |
| opentelemetry-distro | ^0.48 | OTel |
| opentelemetry-exporter-otlp | ^1.27 | OTel export |
| sentry-sdk[fastapi] | ^2.13 | Erros |
| httpx | ^0.27 | Cliente HTTP |
| respx | ^0.21 | Mock HTTPX em testes |
| pytest | ^8.3 | Test framework |
| pytest-asyncio | ^0.24 | Async tests |
| pytest-cov | ^5.0 | Coverage |
| pytest-xdist | ^3.6 | Paralelismo |
| hypothesis | ^6 | Property-based |
| factory-boy | ^3.3 | Fixtures |
| ruff | ^0.6 | Lint + format |
| mypy | ^1.11 | Type check |
| stripe | ^11 | Stripe SDK |
| slowapi | ^0.1.9 | Rate limit |
| email-validator | ^2.2 | Email validation |

### Frontend (TypeScript)

| Pacote | Versão | Função |
|--------|--------|--------|
| next | ^15 | Framework |
| react | ^19 | UI lib |
| typescript | ^5.5 | TS |
| @tanstack/react-query | ^5 | Estado de servidor |
| zustand | ^5 | Estado UI global mínimo |
| @auth/core, next-auth | ^5 (beta estável) | Auth |
| tailwindcss | ^4 | CSS |
| @radix-ui/react-* | latest | Primitives (via shadcn) |
| lucide-react | latest | Ícones |
| recharts | ^2 | Gráficos |
| zod | ^3.23 | Validação |
| react-hook-form | ^7 | Forms |
| next-intl | ^3 | i18n |
| @stripe/stripe-js | ^4 | Stripe Checkout client |
| vitest | ^2 | Unit tests |
| @testing-library/react | ^16 | Component tests |
| playwright | ^1.47 | E2E |
| eslint | ^9 | Lint |
| @biomejs/biome | ^1.9 | Format + lint rápido |
| prettier | ^3 | Format (opcional, biome cobre) |

---

## 2. Por que dessas escolhas

### Python + FastAPI
- **Tipagem forte** com Pydantic v2 (validação automática, OpenAPI grátis).
- **Async I/O** maduro para alta concorrência sem threads.
- **Ecossistema científico** para análises futuras (numpy, pandas, polars, scikit-learn).
- **DX excelente**: hot reload, docs interativas, comunidade enorme.

### Next.js 15 + App Router
- Server Components reduzem JS no cliente.
- Streaming + Suspense para UX rápida.
- SSR para SEO em páginas públicas (landing, pricing).
- Roteamento file-based.

### PostgreSQL via Supabase
- **Supabase** gerencia o Postgres 16: backups automáticos, PITR, painel visual, SQL editor.
- **JSONB** dá flexibilidade onde precisar sem perder ACID.
- **Particionamento por tempo** já testado no Postgres.
- **GIN indexes** ajudam em buscas em arrays e JSONB.
- **Row-Level Security** como segunda barreira de isolamento de tenant — Supabase tem suporte nativo a RLS.
- Migração futura para outro Postgres (Neon, RDS) é `pg_dump | pg_restore` — schema via Alembic garante portabilidade.

### Celery
- **Retries com backoff exponencial** built-in.
- **Routing por fila** (`parsing`, `stats`, `email`).
- **Beat scheduler** para crons internos.
- Mais maduro que Dramatiq/RQ; comunidade ampla.

### Cloudflare R2
- **Zero egress** crítico para downloads (replayer pode buscar HH original).
- Custo baixo previsível.
- API S3-compatível: mesmas SDKs.

### Auth.js v5
- Suporta credentials + OAuth (Google) em um só lugar.
- Sessões em cookies httpOnly.
- Adapter Prisma/Drizzle, mas vamos rolar nosso adapter para usar SQLAlchemy via API.

### Stripe
- BR-friendly (suporta Pix e cartão).
- Boleto via integradores se necessário.
- Webhooks confiáveis com retries.

---

## 3. Convenções de versionamento de dependências

- **SemVer-aware**: usar `^` para libs estáveis (>=1.0), `~` para libs <1.0 (mais conservador).
- Lockfiles **comitados**: `uv.lock`, `pnpm-lock.yaml`.
- **Renovate** ou **Dependabot** configurado para PRs semanais de update menor.
- Updates major: PR dedicado com plano de migração nas notas.

---

## 4. Tooling de desenvolvimento

| Ferramenta | Função | Comando padrão |
|-----------|--------|----------------|
| **uv** | gerencia venv e deps Python | `uv sync`, `uv add <pkg>` |
| **ruff** | lint + format Python | `make lint`, `make format` |
| **mypy --strict** | type check | `make typecheck` |
| **pytest** | testes Python | `make test` |
| **pnpm** | manager Node | `pnpm install` |
| **biome** | lint+format TS | `make lint` |
| **playwright** | E2E | `pnpm test:e2e` |
| **alembic** | migrations | `make migrate` |
| **docker compose** | infra dev | `make dev` |
| **mkcert** | TLS local | opcional |
| **direnv** | env vars por pasta | opcional, recomendado |
| **pre-commit** | hooks Git | `pre-commit install` |

### pre-commit hooks obrigatórios

- ruff (lint + format)
- mypy (rápido, em modified files)
- biome (TS)
- detect-secrets (segurança)
- forbid commit of `.env`, `*.key`, `*.pem`
- pytest collection (verifica sintaxe de testes)

---

## 5. Estrutura de configuração

Toda configuração via **variáveis de ambiente**, lidas por `pokerinsight.core.config.Settings(BaseSettings)`. Nunca `os.getenv` direto.

`.env.example` (na raiz):

```bash
# === App ===
APP_ENV=local                     # local | ci | staging | production
APP_NAME=pokerinsight
APP_LOG_LEVEL=DEBUG               # DEBUG | INFO | WARNING | ERROR
APP_BASE_URL=http://localhost:8000

# === Database ===
DATABASE_URL=postgresql+asyncpg://pokerinsight:dev@localhost:5432/pokerinsight
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10
DATABASE_ECHO=false

# === Redis ===
REDIS_URL=redis://localhost:6379/0
REDIS_CELERY_BROKER=redis://localhost:6379/3
REDIS_CELERY_RESULT=redis://localhost:6379/3
REDIS_CACHE=redis://localhost:6379/0
REDIS_RATELIMIT=redis://localhost:6379/2

# === Object storage ===
S3_ENDPOINT=http://localhost:9000  # MinIO em dev; R2 em prod
S3_REGION=auto
S3_BUCKET_HH=pi-hh-raw
S3_BUCKET_EXPORTS=pi-exports
S3_ACCESS_KEY_ID=minio_dev
S3_SECRET_ACCESS_KEY=minio_dev_secret

# === Auth ===
JWT_PRIVATE_KEY_PATH=/run/secrets/jwt_priv.pem      # RS256
JWT_PUBLIC_KEY_PATH=/run/secrets/jwt_pub.pem
JWT_ACCESS_TTL_SECONDS=900                          # 15min
JWT_REFRESH_TTL_SECONDS=2592000                     # 30d
ARGON2_TIME_COST=3
ARGON2_MEMORY_COST=65536
ARGON2_PARALLELISM=4

# === OAuth Google ===
GOOGLE_OAUTH_CLIENT_ID=
GOOGLE_OAUTH_CLIENT_SECRET=

# === Stripe ===
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
STRIPE_PRO_PRICE_ID=

# === E-mail ===
RESEND_API_KEY=
EMAIL_FROM=no-reply@pokerinsight.app
EMAIL_REPLY_TO=suporte@pokerinsight.app

# === Observabilidade ===
SENTRY_DSN=
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
OTEL_SERVICE_NAME=pokerinsight-api

# === Limites de plano ===
FREE_HANDS_QUOTA_30D=5000
PRO_HANDS_QUOTA_30D=0  # 0 = ilimitado
MAX_UPLOAD_MB_FREE=50
MAX_UPLOAD_MB_PRO=200

# === Frontend (apps/web/.env.local) ===
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=
```

⚠️ **Nunca** commitar `.env`. Sempre `.env.example` atualizado para refletir variáveis disponíveis.

---

## 6. Pinagem de Docker

`Dockerfile` da API:

```dockerfile
FROM python:3.12-slim-bookworm AS base
# pinning OS pacotes via /etc/apt/sources.list.d se necessário
```

`docker compose` usa tags fixas: `postgres:16.4-bookworm`, `redis:7.2-alpine`, `minio/minio:RELEASE.2024-08-XX`.

---

## 7. Pacotes proibidos / cuidado

| Pacote | Por quê | Alternativa |
|--------|---------|-------------|
| `requests` | sync, sem types ricos | `httpx` |
| `psycopg2` | versão sync legada | `asyncpg` ou `psycopg[binary]` v3 |
| `peewee`, `tortoise-orm` | menores | `sqlalchemy` |
| `flask`, `django` | escolhemos FastAPI | n/a |
| Qualquer lib com licença GPL/AGPL forte | conflito com SaaS proprietário | n/a |
| `unsafe-yaml.load` sem `Loader=SafeLoader` | RCE | `yaml.safe_load` |
| `pickle` com input externo | RCE | `json` / `msgpack` |
