# 11 — Deployment e Infraestrutura

> Stack escolhida para simplicidade máxima: **Vercel** (frontend) + **Railway** (API + workers) + **Supabase** (DB) + **Upstash** (Redis). Tudo tem tier gratuito e GitHub integration nativa — os agentes configuram os arquivos, você só cria as contas e cola os tokens.

## 1. Visão Geral da Stack de Deploy

```
GitHub ──push──▶ Vercel (Next.js)        → app.pokerinsight.app
         └────▶ Railway (FastAPI)         → api.pokerinsight.app
         └────▶ Railway (Celery workers)  → processo background

Supabase (Postgres 16)    ← usado por API + workers
Upstash (Redis serverless) ← usado por API + workers + cache
Cloudflare R2             ← arquivos HH
Resend                    ← emails
Stripe                    ← pagamentos
```

Ambas as plataformas (Vercel e Railway) detectam o push no GitHub e fazem deploy automático. Você não precisa rodar comando nenhum no dia a dia — só na primeira configuração.

---

## 2. Ambientes

| Ambiente | URL | Branch | Auto-deploy | Acesso |
|---|---|---|---|---|
| `dev` | localhost | feature/* | — | local |
| `preview` | gerado por Vercel/Railway | PR | sim (preview) | time |
| `staging` | staging.pokerinsight.app | `main` | sim | time + beta |
| `prod` | app.pokerinsight.app | tag `v*.*.*` | manual approval | público |

---

## 3. Plataformas e Custos

### 3.1 Vercel (Frontend — Next.js)
- **Tier gratuito (Hobby)**: ilimitado para projetos pessoais/MVP.
  - 100GB bandwidth/mês, 6.000 builds/mês — mais que suficiente.
- **Tier Pro ($20/mês)**: necessário se quiser team members ou domínio customizado em org.
- **Domínio**: conectar `app.pokerinsight.app` no painel (1 clique).
- **O que os agentes configuram**: `vercel.json`, variáveis de ambiente via CLI.
- **O que você faz uma vez**: criar conta, conectar repo, colar o domínio.

### 3.2 Railway (Backend API + Workers)
- **Tier gratuito**: $5 de crédito por mês — suficiente para MVP pequeno (API leve + 1 worker).
- **Tier Hobby ($5/mês)**: remove o limite de crédito; ~$10-30/mês de uso real.
- **Como funciona**: você cria um "Project", dentro dele cria "Services" (um para API, um para Worker). Cada service é um processo Docker.
- **GitHub integration**: push em `main` → deploy automático.
- **O que os agentes configuram**: `railway.toml`, Dockerfile, variáveis de ambiente.
- **O que você faz uma vez**: criar conta, conectar repo, criar services, colar secrets.

### 3.3 Supabase (Postgres 16)
- **Tier gratuito**: 500MB storage, 2 projetos, **pausa após 7 dias sem acesso** (ruim pra prod).
- **Tier Pro ($25/mês)**: sem pausa, 8GB storage, PITR 7 dias — necessário em staging/prod.
- **O que os agentes configuram**: migrations Alembic (rodam no deploy), `DATABASE_URL`.
- **O que você faz uma vez**: criar projeto, copiar `DATABASE_URL` e `SERVICE_ROLE_KEY`.
- **Painel útil**: SQL editor, Table editor, Logs — ótimo para debug.

### 3.4 Upstash (Redis serverless)
- **Tier gratuito**: 10.000 comandos/dia — suficiente para MVP.
- **Pay-as-you-go**: $0.2 por 100k comandos após isso. Custo real: centavos.
- **O que os agentes configuram**: `REDIS_URL` nas variáveis.
- **O que você faz uma vez**: criar database, copiar URL.

### 3.5 Cloudflare R2 (Storage)
- **Tier gratuito**: 10GB storage, 1M requests/mês, **egress zero** sempre.
- **O que os agentes configuram**: bucket name, CORS policy, políticas de presigned URL.
- **O que você faz uma vez**: criar bucket, gerar API token com permissões de leitura/escrita.

### Custo total estimado por fase

| Fase | Usuários | Custo/mês | Stack ativa |
|---|---|---|---|
| **Desenvolvimento** | 0 | **$0** | Tudo free tier |
| **MVP launch** | até 500 MAU | **$0–$30** | Supabase Pro ($25) + Railway Hobby ($5) |
| **Beta crescendo** | até 5k MAU | **~$60** | + Railway scale |
| **Crescimento** | até 50k MAU | **~$200** | Supabase Pro maior, Railway escala, Upstash pago |

---

## 4. O que os Agentes Fazem vs O que Você Faz

### Você faz uma vez (setup inicial — ~1 hora)

```
1. Criar conta Vercel → vercel.com → "Add New Project" → conectar GitHub
2. Criar conta Railway → railway.app → "New Project" → conectar GitHub
3. Criar projeto Supabase → supabase.com → copiar DATABASE_URL
4. Criar DB Upstash → upstash.com/redis → copiar REDIS_URL
5. Criar bucket R2 → cloudflare.com → R2 → copiar credenciais
6. Criar conta Resend → resend.com → gerar API key
7. Criar conta Stripe → stripe.com → pegar keys de test mode
8. Colar todas as variáveis de ambiente no Railway e Vercel (painel web)
```

### Os agentes fazem (sem intervenção sua)

```
✅ Escrever railway.toml (config de deploy da API e do worker)
✅ Escrever vercel.json (config de rotas, redirects, headers)
✅ Escrever Dockerfiles (API + Worker)
✅ Configurar GitHub Actions (testes, lint, pipeline)
✅ Escrever script de migrate (roda alembic upgrade head no deploy)
✅ Configurar CORS, CSP, headers de segurança
✅ Qualquer mudança de config após o setup inicial
✅ Adicionar novas variáveis de ambiente (via arquivo, você cola no painel)
```

---

## 5. Arquivos de Configuração (gerados pelos agentes)

### railway.toml
```toml
[build]
builder = "dockerfile"
dockerfilePath = "apps/api/Dockerfile"

[[services]]
name = "api"
[services.deploy]
startCommand = "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/healthz"
healthcheckTimeout = 30
restartPolicyType = "on_failure"

[[services]]
name = "worker-parsing"
[services.deploy]
startCommand = "celery -A app.worker.celery_app worker -Q parsing,stats -c 4"
```

### vercel.json
```json
{
  "framework": "nextjs",
  "buildCommand": "pnpm build",
  "outputDirectory": ".next",
  "rewrites": [
    { "source": "/api/:path*", "destination": "https://api.pokerinsight.app/:path*" }
  ],
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        { "key": "X-Frame-Options", "value": "DENY" },
        { "key": "X-Content-Type-Options", "value": "nosniff" },
        { "key": "Referrer-Policy", "value": "strict-origin-when-cross-origin" }
      ]
    }
  ]
}
```

### apps/api/Dockerfile
```dockerfile
FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY apps/api/app ./app
RUN useradd -u 10001 -r appuser && chown -R appuser /app
USER 10001
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 6. Variáveis de Ambiente (onde colar)

### No Railway (API + Worker)
```bash
# Supabase
DATABASE_URL=postgresql+asyncpg://postgres.[ref]:[password]@aws-0-us-east-1.pooler.supabase.com:5432/postgres

# Upstash Redis
REDIS_URL=rediss://default:[password]@[endpoint].upstash.io:6379

# R2 / S3
R2_ENDPOINT_URL=https://[account-id].r2.cloudflarestorage.com
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET_NAME=pokerinsight-prod

# JWT
JWT_PRIVATE_KEY=...    # gerado pelos agentes: openssl genrsa -out private.pem 2048
JWT_PUBLIC_KEY=...

# Stripe
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Resend
RESEND_API_KEY=re_...

# App
APP_ENV=production
APP_URL=https://app.pokerinsight.app
API_URL=https://api.pokerinsight.app
```

### Na Vercel (Frontend)
```bash
NEXT_PUBLIC_API_URL=https://api.pokerinsight.app
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_...
```

---

## 7. Fluxo de Deploy (dia a dia após setup)

### Deploy normal (automático)
```
1. Você (ou agente) faz commit + push na branch feature/...
2. Abre PR
3. Vercel cria preview URL do frontend automaticamente
4. Railway cria preview do backend automaticamente
5. CI roda testes (GitHub Actions)
6. PR aprovado → merge em main
7. Vercel e Railway fazem deploy em staging automaticamente
8. Smoke tests rodam
9. Você testa em staging.pokerinsight.app
10. Cria tag v1.2.3 → deploy em prod (requer approve no GitHub)
```

### Primeira vez (setup do zero — os agentes guiam)
```
# 1. Instalar CLIs (agente gera o script)
npm i -g vercel railway

# 2. Login
vercel login
railway login

# 3. Linkar projetos (uma vez)
cd apps/web && vercel link
cd apps/api && railway link

# 4. Deploy manual inicial
vercel --prod          # frontend
railway up             # backend
```

---

## 8. Migrations no Deploy

O Railway roda um comando de release antes de trocar a versão:

```toml
# railway.toml
[deploy]
releaseCommand = "alembic upgrade head"
```

Isso garante que as migrations rodam **antes** da nova versão da API subir. Se falhar, o deploy aborta e a versão antiga continua rodando.

---

## 9. Rollback

### Frontend (Vercel)
Painel Vercel → Deployments → clique em qualquer deploy anterior → "Promote to Production". Leva ~10 segundos.

### Backend (Railway)
Painel Railway → Service → Deployments → clique no deploy anterior → "Rollback". Leva ~30 segundos.

Não existe comando mais simples que esse.

---

## 10. Monitoramento no Supabase

O painel do Supabase já inclui:
- **Logs** de queries (aba "Logs → Database").
- **Query performance** — queries lentas destacadas.
- **Métricas** de conexões, CPU, IOPS.
- **Backups automáticos** diários (Pro plan).
- **SQL Editor** — útil para debug manual.

Para o MVP, esse painel substitui boa parte do que seria necessário configurar manualmente em Grafana.

---

## 11. Domínio Customizado

### Vercel
1. Painel Vercel → Project → Settings → Domains → adicionar `app.pokerinsight.app`.
2. Vercel mostra o DNS record a criar.
3. No Cloudflare (DNS): criar CNAME apontando para o valor que a Vercel mostrou.
4. Pronto, HTTPS automático.

### Railway
1. Painel Railway → Service (api) → Settings → Networking → Add Custom Domain.
2. Adicionar `api.pokerinsight.app`.
3. Mesmo processo: CNAME no Cloudflare.

---

## 12. Sem Terraform no MVP

O MVP **não usa Terraform**. Motivo: a complexidade não compensa para 2-3 serviços que têm painéis web excelentes. Terraform entra quando você tiver:
- Múltiplos ambientes idênticos para replicar.
- Mais de 5-6 recursos de infraestrutura para gerenciar.
- Time de infra dedicado.

O que está versionado no repo para infra:
- `railway.toml` — config do Railway.
- `vercel.json` — config da Vercel.
- `Dockerfile` — imagem da API.
- `infra/compose.dev.yml` — ambiente local.
- `.github/workflows/` — CI/CD.

---

## 13. Disaster Recovery

| Cenário | Solução | Tempo |
|---|---|---|
| Bug em prod (frontend) | Rollback no painel Vercel | 10s |
| Bug em prod (backend) | Rollback no painel Railway | 30s |
| Dados corrompidos | Restore via Supabase PITR | 5-30min |
| Supabase fora | Connection string aponta para backup | 15min |
| Railway fora | Re-deploy em Render (mesmo Dockerfile) | 20min |
