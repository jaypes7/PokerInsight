# PokerInsight — SaaS de Análise de Hand Histories (HH) de Poker

> **Status**: 📐 Documentação inicial / Pré-MVP
> **Tipo**: SaaS multi-tenant, web (mobile-responsive)
> **Foco do MVP**: Análise de HH de torneios **PokerStars (PT-BR)** — No Limit Hold'em
> **Co-piloto de codificação**: OpenAI Codex + Anthropic Claude Code

---

## 1. Visão geral em 30 segundos

PokerInsight é um SaaS que ingere arquivos de Hand History (HH) gerados pelo cliente PokerStars, faz parsing estruturado, calcula estatísticas (VPIP, PFR, 3-bet%, AF, WTSD, W$SD, EV, etc.), e entrega ao jogador um painel com filtros, replayer de mãos e relatórios de leak-finder.

**Diferencial técnico**: parser robusto para o formato em **português brasileiro** (a maioria dos trackers existentes — PokerTracker, Hold'em Manager — tem suporte limitado ou bugs com HH em PT-BR).

**Proposta de valor inicial**: dashboard simples e barato, focado em micro-stakes brasileiros, sem precisar instalar nada (web-first).

---

## 2. Como ler esta documentação

A documentação está dividida em arquivos pequenos para que os agentes de IA (Codex / Claude Code) carreguem apenas o que precisam em cada tarefa. **Sempre comece por `AGENTS.md`** para entender o protocolo de trabalho dos agentes.

| Arquivo | Quando ler |
|--------|------------|
| [`AGENTS.md`](./AGENTS.md) | **Antes de qualquer tarefa** — convenções, branching, PR, definição de pronto |
| [`TODO.md`](./TODO.md) | **A cada tarefa** — pegar próxima task, marcar concluída |
| [`docs/01-PRD.md`](./docs/01-PRD.md) | Entender o produto, personas, escopo do MVP |
| [`docs/02-ARCHITECTURE.md`](./docs/02-ARCHITECTURE.md) | Visão de arquitetura, componentes, fluxos |
| [`docs/03-TECH-STACK.md`](./docs/03-TECH-STACK.md) | Quais ferramentas, versões e bibliotecas usar |
| [`docs/04-DATA-MODEL.md`](./docs/04-DATA-MODEL.md) | Schema do banco, ERD, migrations |
| [`docs/05-HH-PARSER-SPEC.md`](./docs/05-HH-PARSER-SPEC.md) | **Crítico** — gramática, regex, tokens do HH PokerStars PT-BR |
| [`docs/06-POKER-STATS-SPEC.md`](./docs/06-POKER-STATS-SPEC.md) | Fórmulas exatas de VPIP, PFR, 3-bet%, AF, etc. |
| [`docs/07-API-SPEC.md`](./docs/07-API-SPEC.md) | Contratos REST/JSON, exemplos de request/response |
| [`docs/08-SECURITY.md`](./docs/08-SECURITY.md) | Modelo de ameaças, autenticação, criptografia, LGPD |
| [`docs/09-TESTING-CICD.md`](./docs/09-TESTING-CICD.md) | Estratégia de testes e pipeline CI/CD |
| [`docs/10-PERFORMANCE.md`](./docs/10-PERFORMANCE.md) | Otimização de queries, índices, cache, batch processing |
| [`docs/11-DEPLOYMENT.md`](./docs/11-DEPLOYMENT.md) | Infra, ambientes, IaC, runbooks |
| [`docs/12-OBSERVABILITY.md`](./docs/12-OBSERVABILITY.md) | Logs, métricas, traces, alertas |
| [`docs/13-GLOSSARY.md`](./docs/13-GLOSSARY.md) | Glossário de poker PT ↔ EN, termos técnicos |

---

## 3. Stack resumida

| Camada | Tecnologia | Por quê |
|--------|------------|--------|
| Frontend | Next.js 15 (App Router) + TypeScript + Tailwind + shadcn/ui + TanStack Query | SSR/SSG, ecossistema React maduro, primitives acessíveis |
| Backend API | Python 3.12 + FastAPI + Pydantic v2 | Tipagem forte, async nativo, ótimo para parsing/analytics |
| ORM | SQLAlchemy 2.0 (async) + Alembic | Padrão Python, migrações versionadas |
| Banco principal | PostgreSQL 16 | ACID, JSONB, índices parciais, particionamento, GIN |
| Cache / Sessões / Broker | Redis via Upstash | Performance, suporte a streams e pub/sub; serverless free tier |
| Workers (parsing pesado) | Celery 5 + Redis broker | Filas, retries, schedules |
| Storage de arquivos brutos | S3-compatível (Cloudflare R2 no início) | Custo baixo, durabilidade |
| Auth | Auth.js no front + JWT (RS256) com refresh rotativo no back | Padrão, suporte OAuth |
| Pagamentos | Stripe | Subscriptions, webhooks, BR aceito |
| E-mail transacional | Resend | DX simples, deliverability |
| Observabilidade | OpenTelemetry + Grafana Cloud + Sentry | Open standards, custo previsível |
| CI/CD | GitHub Actions + Docker | Padrão de mercado |
| Deploy Frontend | Vercel | GitHub integration nativa; free tier robusto; você já conhece |
| Deploy Backend | Railway | GitHub integration; Dockerfile; free $5 crédito/mês |
| Banco de Dados | Supabase | Postgres 16 gerenciado; PITR; painel visual; free → Pro $25/mês |

Detalhes e justificativas: [`docs/03-TECH-STACK.md`](./docs/03-TECH-STACK.md).

---

## 4. Estrutura do monorepo (proposta)

```
pokerinsight/
├── apps/
│   ├── api/                    # FastAPI backend
│   │   ├── src/
│   │   │   ├── pokerinsight/
│   │   │   │   ├── api/        # routers
│   │   │   │   ├── core/       # config, security, deps
│   │   │   │   ├── db/         # SQLAlchemy models, repositories
│   │   │   │   ├── domain/     # entidades de domínio
│   │   │   │   ├── parsers/    # HH parser (PokerStars PT-BR)
│   │   │   │   ├── stats/      # cálculo de estatísticas
│   │   │   │   ├── services/   # casos de uso
│   │   │   │   ├── tasks/      # Celery tasks
│   │   │   │   └── main.py
│   │   ├── tests/
│   │   ├── alembic/            # migrations
│   │   ├── pyproject.toml
│   │   └── Dockerfile
│   └── web/                    # Next.js frontend
│       ├── src/
│       │   ├── app/
│       │   ├── components/
│       │   ├── lib/
│       │   └── styles/
│       ├── tests/
│       ├── package.json
│       └── Dockerfile
├── packages/
│   ├── hh-fixtures/            # arquivos HH de teste (anonimizados)
│   └── shared-types/           # tipos compartilhados (zod schemas, etc.)
├── infra/
│   ├── terraform/
│   ├── docker-compose.yml      # ambiente local
│   └── docker-compose.test.yml
├── .github/
│   └── workflows/              # pipelines CI/CD
├── docs/                       # ⬅ documentação (este diretório)
├── AGENTS.md
├── TODO.md
└── README.md
```

---

## 5. Quick start (local)

> Pré-requisitos: Docker + Docker Compose, Node 20+, Python 3.12+, uv (`pip install uv`)

```bash
git clone <repo>
cd pokerinsight
cp .env.example .env
docker compose -f infra/docker-compose.yml up -d postgres redis minio
cd apps/api && uv sync && uv run alembic upgrade head && uv run uvicorn pokerinsight.main:app --reload
# em outra aba:
cd apps/web && pnpm install && pnpm dev
```

Endpoints:
- API: http://localhost:8000 (docs em `/docs`)
- Web: http://localhost:3000
- MinIO console: http://localhost:9001

---

## 6. Princípios de produto e engenharia

1. **Privacidade por padrão**: HH contém padrões de jogo do usuário; é dado sensível. Criptografia em trânsito e em repouso. Multi-tenant rigoroso.
2. **Performance é feature**: jogadores grindam dezenas de milhares de mãos por mês. Importar 100k mãos deve levar minutos, não horas.
3. **Correção > velocidade de entrega**: parser errado = stats erradas = produto morto. Cobertura de testes alta no parser e nos cálculos.
4. **Mobile-first responsivo**: muitos jogadores BR consultam stats no celular.
5. **Roadmap de pokers além do Stars**: arquitetura permite plugar parsers para GGPoker, Partypoker, etc. em versões futuras.

---

## 7. Roadmap em uma página

| Fase | Conteúdo | Critério de saída |
|------|----------|-------------------|
| **F0 — Foundation** | Repo, CI básico, infra dev, auth básica | Lint+test passando em CI; deploy de "hello world" em staging |
| **F1 — Parser + Storage** | Parser PokerStars PT-BR completo, upload de arquivos, persistência | Importar HH de teste e ver mão estruturada na API |
| **F2 — Stats core** | VPIP, PFR, 3-bet%, fold to 3-bet%, AF, WTSD, W$SD | Dashboard com 7 stats principais por jogador |
| **F3 — Frontend MVP** | Login, upload, dashboard, lista de sessões, replayer | Jogador faz onboarding sozinho e vê stats |
| **F4 — Cobrança & limites** | Stripe, planos free/pro, rate limit, quotas | Cobra cartão e libera tier pago |
| **F5 — Polish & launch** | Observabilidade, runbooks, LGPD docs, SEO | Beta privado convidado |

Detalhes: [`docs/01-PRD.md`](./docs/01-PRD.md) e [`TODO.md`](./TODO.md).

---

## 8. Licença & contribuição

Projeto privado. Veja `AGENTS.md` para o protocolo de contribuição dos agentes de IA.
