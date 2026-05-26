# 12 — Observabilidade

> Não dá pra operar o que não dá pra medir. Toda feature precisa **logar, tracear, e (quando aplicável) emitir métrica** antes de ir pra prod.

## 1. Pilares

| Pilar | Backend | Stack |
|---|---|---|
| Logs | API, Workers | structlog → JSON stdout → Grafana Loki |
| Métricas | API, Workers, DB | OpenTelemetry → Grafana Cloud Prometheus |
| Traces | API, Workers, DB queries | OpenTelemetry → Grafana Cloud Tempo |
| Errors | API, Web | Sentry |
| Uptime | externo | Cloudflare Healthchecks + Statuspage |

## 2. Logging Estruturado

### 2.1 Setup
```python
# apps/api/app/observability/logging.py
import structlog, logging, sys

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.dict_tracebacks,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
    cache_logger_on_first_use=True,
)
log = structlog.get_logger()
```

### 2.2 Campos obrigatórios em toda linha
- `timestamp` (UTC ISO 8601).
- `level` (`debug`/`info`/`warning`/`error`/`critical`).
- `service` (`api` / `worker` / `web`).
- `env` (`dev`/`staging`/`prod`).
- `version` (semver + git sha).
- `request_id` (UUID v7; gerado em middleware; propagado pelo header `X-Request-ID`).
- `trace_id`, `span_id` (do OTel context).
- `user_id` (quando autenticado).

### 2.3 Middleware (FastAPI)
```python
@app.middleware("http")
async def log_context(request, call_next):
    rid = request.headers.get("x-request-id") or str(uuid7())
    structlog.contextvars.bind_contextvars(
        request_id=rid,
        method=request.method,
        path=request.url.path,
    )
    t = time.monotonic()
    try:
        resp = await call_next(request)
    except Exception:
        log.exception("request_failed")
        raise
    finally:
        log.info("request", status=resp.status_code, latency_ms=int((time.monotonic()-t)*1000))
        structlog.contextvars.clear_contextvars()
    resp.headers["X-Request-ID"] = rid
    return resp
```

### 2.4 Níveis — quando usar cada um
- `debug`: detalhe granular; **desligado em prod** por padrão.
- `info`: evento esperado (request, task started/done, login).
- `warning`: anômalo mas recuperável (retry, rate limit hit, parser unknown line tolerado).
- `error`: falha que afeta usuário (request 5xx, task falhou após retries).
- `critical`: incidente, alerta humano (DB down, key rotation falhou).

### 2.5 Proibido em logs (ver §10 do `08-SECURITY.md`)
- Senha (mesmo hash).
- Token JWT completo (apenas `jti` ou primeiros 8 chars).
- Refresh token.
- PAN/CVV (Stripe nunca envia para nós; é só princípio).
- Body completo de uploads.

## 3. Tracing (OpenTelemetry)

### 3.1 Instrumentação automática
- `opentelemetry-instrumentation-fastapi`
- `opentelemetry-instrumentation-sqlalchemy`
- `opentelemetry-instrumentation-asyncpg`
- `opentelemetry-instrumentation-redis`
- `opentelemetry-instrumentation-celery`
- `opentelemetry-instrumentation-httpx`

### 3.2 Spans manuais
- Parser: 1 span por hand (`parser.hand`), com attrs `hand.site_id`, `hand.streets_count`.
- Stats compute: span `stats.compute` com attr `stats.filter_hash`.
- Stripe webhook: span `webhook.stripe` com attr `event.type`.

### 3.3 Sampling
- Prod: 10% trace sample para requests; 100% para errors.
- Staging: 100%.

### 3.4 Exporter
- OTLP gRPC → Grafana Cloud Tempo.
- `OTEL_RESOURCE_ATTRIBUTES=service.name=api,service.version=...,env=prod`.

## 4. Métricas

### 4.1 RED por endpoint
- **R**ate: requests/s por rota+método.
- **E**rrors: 5xx/s.
- **D**uration: p50/p95/p99.

Coletado via OTel + `opentelemetry-instrumentation-fastapi` (histograma `http.server.duration`).

### 4.2 Métricas de negócio (custom)
```python
from opentelemetry import metrics
meter = metrics.get_meter("pokerinsight.api")

hands_parsed = meter.create_counter("hands_parsed_total")
parser_errors = meter.create_counter("parser_errors_total")
import_duration = meter.create_histogram("import_duration_seconds")
active_users = meter.create_observable_gauge("active_users", callbacks=[count_dau])
mrr_cents = meter.create_observable_gauge("mrr_cents", callbacks=[compute_mrr])
```

### 4.3 Métricas de sistema
- DB: connections used, query duration, slow queries, locks.
- Redis: ops/s, memory, evictions.
- Queue Celery: depth por queue, task duration, failure rate.

### 4.4 SLIs e SLOs

| SLI | SLO (rolling 30d) |
|---|---|
| Disponibilidade `GET /v1/hands` | 99.5% (5xx<0.5%) |
| Latência `GET /v1/hands` p95 | <500ms em 95% dos minutos |
| Taxa de sucesso de imports | >99% (entre `complete` e `processed`) |
| Disponibilidade frontend | 99.9% (CDN) |

Error budget: 0.5% mês → ~3.6h de downtime tolerado. Esgotou? Feature freeze, foco em estabilidade.

## 5. Sentry (Errors)

### 5.1 Backend
- DSN em env var; sample rate 100% para errors, 10% para traces.
- `before_send` redacta campos sensíveis (autorization, cookies, tokens).
- `release` setado para git SHA (associa stack ao código exato).
- Source maps Python: opcional.

### 5.2 Frontend
- `@sentry/nextjs`.
- Source maps enviados em build (com auth token; **não** comitados).
- `tracesSampleRate: 0.1` em prod.
- `replaysSessionSampleRate: 0.01`, `replaysOnErrorSampleRate: 1.0` (replay só em erro).

### 5.3 Filtros
- Erros conhecidos não bloqueantes: `ChunkLoadError` (browser stale), `ResizeObserver loop limit` (benign).
- Bots: `ignoreErrors` para user-agents conhecidos.

## 6. Dashboards (Grafana)

Dashboards versionados em JSON em `infra/grafana/dashboards/`.

### 6.1 Overview
- Painéis: req/s, error rate, p50/p95/p99, latência por endpoint top 10, DB connections, Redis hit ratio, queue depth.
- Variáveis: `env`, `service`.
- Time range padrão: last 1h.

### 6.2 Parser
- Hands/s, errors/s, duração média, distribuição de "unknown line" tags.

### 6.3 Business
- DAU, WAU, MAU.
- Conversão Free→Pro semanal.
- Churn mensal.
- MRR/ARR.
- Hands analisadas /dia.

### 6.4 Infra
- CPU/RAM/IO por serviço.
- DB: tps, slow queries, replication lag, cache hit ratio.
- Redis: memory, evictions, ops/s.

## 7. Alertas

| Alerta | Condição | Severidade | Canal |
|---|---|---|---|
| API down | health check falha 3x em 5min | Critical | PagerDuty/SMS |
| Error rate alto | 5xx > 1% por 10min | High | Slack #alerts |
| p95 alto | p95 > 2s por 15min em endpoint crítico | High | Slack #alerts |
| DB CPU alto | >85% por 15min | Medium | Slack #ops |
| Queue Celery cresce | depth > 1000 por 10min | Medium | Slack #ops |
| Parser erro alto | unknown_line rate > 0.5% | Medium | Slack #parser |
| Disco baixo | <15% livre | High | Slack #ops |
| Stripe webhook falhando | failure rate > 5% por 30min | High | Slack #alerts |
| Cache hit ratio baixo | <70% por 1h | Low | Slack #ops |
| MRR anômalo | -10% week-over-week | Medium | Slack #business |

Política: todo alerta tem **runbook** linkado. Alerta sem runbook é proibido (cria fadiga).

## 8. Healthchecks Externos

- Cloudflare Health Check (built-in) faz GET `/healthz` a cada 30s de 3 regiões.
- Statuspage Cloudflare incidentes públicos em `status.pokerinsight.app`.
- UptimeRobot ou Better Stack como backup independente (não no mesmo provedor da prod).

## 9. Auditoria

- `audit_logs` table inserida sempre que: login, password change, OAuth link, plan change, account delete, export LGPD, admin impersonate, admin role change.
- Linhas imutáveis; nenhum endpoint update/delete em `audit_logs`.
- Stream para sink offsite (S3/R2) diariamente para preservação independente.

## 10. Web Vitals e Frontend RUM

- Coleta via `web-vitals` lib → endpoint `POST /v1/metrics/vitals` (sampled 10%).
- Métricas: LCP, INP, CLS, FCP, TTFB.
- Painel Grafana específico por página.
- Sentry Performance para spans no browser (navegação, custom).

## 11. Frontend Logging

- Em prod, console é silenciado exceto erros (capturados via Sentry).
- Eventos analytics: PostHog ou Plausible (a definir em ADR-010); event-based, opt-in via cookie banner.

## 12. Práticas

- "Log o que você não pode reconstruir depois": evento de negócio (login, upload completed, plan changed).
- "Não log o que está nos traces": detalhes de query individual (já no Tempo).
- Adicione campo, não use mensagem livre: `log.info("import_started", import_id=...)`, não `f"started {id}"`.
- Cardinalidade controlada: nunca use `user_id` como label de métrica (custo Prometheus explode).
- Toda exceção `except` que loga deve **re-raise** ou ter justificativa explícita no comentário.
