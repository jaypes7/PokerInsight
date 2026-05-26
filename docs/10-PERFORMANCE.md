# 10 — Performance e Otimização

> Performance é requisito funcional. Toda query que toca `hands` ou `actions` precisa de plano analisado **antes** de ir para prod.

## 1. Orçamentos (Budgets)

| Métrica | Alvo | Hard limit |
|---|---|---|
| `GET /v1/hands` (listagem 50 itens, user com 100k hands) p95 | <500ms | 2s |
| `GET /v1/hands/{id}` p95 | <100ms | 500ms |
| `GET /v1/stats` (último mês) p95 | <800ms | 3s |
| `POST /v1/imports/{id}/complete` (10k hands) | <60s | 5min |
| Parser throughput | >1000 hands/s | 500 hands/s |
| Frontend LCP (dashboard) | <2.5s | 4s |
| Frontend TBT | <200ms | 600ms |
| Frontend bundle JS first-load | <250KB gzip | 500KB |

Falha de budget no CI bench → bloqueio de merge.

## 2. Regras de Query (obrigatórias)

### 2.1 Sempre filtrar por `user_id`
Toda query em tabela multi-tenant **começa** com `WHERE user_id = :uid`. Sem exceção. RLS é defesa em profundidade, não primária.

### 2.2 EXPLAIN obrigatório
Para qualquer query nova ou alterada em `hands`, `actions`, `hand_players`, `imports` (ou JOIN entre elas), incluir no PR:
- `EXPLAIN (ANALYZE, BUFFERS)` em dataset de teste (100k hands de seed).
- Custo total <500 unidades; sem `Seq Scan` em tabelas grandes.

### 2.3 Sem N+1
- Em SQLAlchemy, usar `selectinload`/`joinedload` explicitamente.
- Endpoint que retorna lista nunca dispara query por item — agregar antes.
- Lint: `sqlalchemy-utils` ou checagem manual em review.

### 2.4 Batch sempre que possível
- Inserts: `INSERT ... VALUES (...), (...), ...` em lotes de **1000 linhas/transação**.
- Updates: `UPDATE ... WHERE id IN (...)` ou `executemany`.
- Deletes idem.
- Parser insere `hands`+`hand_players`+`actions` em transação única por chunk de 500 hands.

### 2.5 Paginação por cursor (não offset)
- Offset alto vira O(n). Usar cursor: `WHERE (played_at, id) < (:last_played_at, :last_id) ORDER BY played_at DESC, id DESC LIMIT 50`.
- Cursor é base64url de `{played_at}:{id}`; opaco para cliente.

### 2.6 Money é BIGINT em cents
- Nunca FLOAT/NUMERIC para cálculo crítico (centavos).
- Soma/agregação no DB com `SUM(hero_net_cents)` sem CAST.

## 3. Indexação

### 3.1 Princípios
- Index alinhado com filtro **e** ordenação (`WHERE x = ? ORDER BY y DESC` → `(x, y DESC)`).
- Partial index quando aplicável (`WHERE went_to_showdown = true`).
- Sem index "para o caso de": cada index custa em write e em storage. Justificar com query real.

### 3.2 Mínimo obrigatório (já em `04-DATA-MODEL.md`)
```sql
CREATE INDEX idx_hands_user_played ON hands (user_id, played_at DESC);
CREATE INDEX idx_hands_user_session ON hands (user_id, session_id);
CREATE INDEX idx_hands_user_buyin ON hands (user_id, buyin_cents) WHERE game_type = 'tournament';
CREATE UNIQUE INDEX idx_hands_user_site_hand ON hands (user_id, site_hand_id);
CREATE INDEX idx_actions_hand ON actions (hand_id, sequence);
CREATE INDEX idx_hand_players_hand ON hand_players (hand_id);
CREATE INDEX idx_hand_players_user_hero ON hand_players (user_id) WHERE is_hero = true;
CREATE INDEX idx_imports_user_status ON imports (user_id, status, created_at DESC);
CREATE INDEX idx_audit_user_created ON audit_logs (user_id, created_at DESC);
```

### 3.3 Stats columns denormalizados
Em `hands`: `h_saw_flop`, `h_vpip`, `h_pfr`, `h_three_bet`, `h_faced_three_bet`, `h_folded_to_three_bet`, `h_postflop_bets`, `h_postflop_raises`, `h_postflop_calls`, `h_wtsd`, `h_w_sd`, `h_net_cents`.
- Calculados pelo parser → escritos junto da hand.
- Permitem agregação em **uma query** sem JOIN em `actions`.

### 3.4 Partial indexes para hero analysis
```sql
CREATE INDEX idx_hands_hero_vpip ON hands (user_id, played_at DESC) WHERE h_vpip = true;
CREATE INDEX idx_hands_hero_3bet ON hands (user_id, played_at DESC) WHERE h_three_bet = true;
```

## 4. Particionamento (Roadmap)

Acima de 50M linhas em `hands`, particionar por mês:
```sql
CREATE TABLE hands (...) PARTITION BY RANGE (played_at);
CREATE TABLE hands_2026_05 PARTITION OF hands FOR VALUES FROM ('2026-05-01') TO ('2026-06-01');
```
- Disparado por job mensal que cria partição do próximo mês.
- `actions` herda particionamento via FK + partição manual.
- Pre-MVP: **não** particionar; complica migrations e ainda não justifica.

## 5. Connection Pooling

- API → DB: **pgbouncer** em transaction mode na borda do Postgres.
  - `max_client_conn=2000`, `default_pool_size=20` por DB.
- Pool no app: `SQLAlchemy create_async_engine(pool_size=10, max_overflow=10, pool_recycle=300)`.
- Workers Celery: pool por processo, não compartilhado entre forks.
- **Nunca** transação > 5s; queries longas em worker, não em HTTP request.

## 6. Cache (Redis)

### 6.1 Camadas

| Camada | Conteúdo | TTL | Invalidação |
|---|---|---|---|
| L1 (in-process LRU) | Schemas, configs, feature flags | 60s | Pull |
| L2 (Redis) | Stats agregados, sessões resumo | 1h-24h | Por evento (import complete → invalida user) |
| L3 (DB `stats_snapshots`) | Stats periódicas (diário) | persistente | Job noturno recalcula |

### 6.2 Chaves
- Padrão: `pi:{env}:{kind}:{user_id}:{hash_dos_filtros}`.
- Exemplo: `pi:prod:stats:u_abc123:30d:tournament:all`.
- Hash dos filtros: SHA-1 dos params normalizados ordenados (curto).

### 6.3 Stampede protection
- Locks com `SET NX EX` (Redis) para recomputo único.
- Cache-aside; nunca cache-as-source-of-truth.

### 6.4 Invalidations
- `import.completed(user_id)` → `DEL pi:prod:stats:{user_id}:*` (via SCAN com cursor; ou tags Redis 8).
- `subscription.changed(user_id)` → idem para chaves de billing.

## 7. Parser Performance

### 7.1 Streaming
- Não carregar arquivo inteiro em memória.
- Iterar linha a linha via generator.
- Splitter emite `HandDraft` para o pipeline a cada hand completa.

### 7.2 Regex
- Compilar **uma vez** em module-level (`re.compile`).
- Preferir `match` vs `search` quando ancorado.
- Para hot path (action lines), avaliar `regex` lib se profiling indicar.

### 7.3 Batch DB
- Buffer de 500 hands → 1 transação com bulk insert (`session.add_all` + `flush` ou `INSERT ... VALUES`).
- Após cada chunk, `session.expunge_all()` para liberar identity map.

### 7.4 Paralelismo
- Por **import**: parser single-process, mas múltiplos imports concorrentes em workers Celery diferentes.
- Por **arquivo**: dividir só se ≥100MB (split em boundary de hand) — out of scope MVP.

### 7.5 Benchmark
```python
# apps/api/tests/benchmarks/test_parser_perf.py
def test_parser_throughput(benchmark, fixture_10k_hands):
    result = benchmark(lambda: list(parse_stream(fixture_10k_hands)))
    assert benchmark.stats['mean'] < 10.0  # 10k hands em <10s = >1k/s
```

## 8. Frontend Performance

### 8.1 Next.js
- **App Router** com RSC por padrão; Client Components só para interatividade.
- `loading.tsx` + Suspense em rotas pesadas.
- `next/dynamic` para replayer (heavy lib carregada sob demanda).
- Streaming SSR habilitado.

### 8.2 Bundle
- Análise via `@next/bundle-analyzer` em cada release.
- Limite hard: 250KB gzip no entry; alerta em PR se ultrapassar.
- Imports tree-shakeable apenas (`import { foo } from 'lib'`, nunca `import * as X`).

### 8.3 Data
- TanStack Query: `staleTime` agressivo (60s para listas, 5min para stats).
- Optimistic updates para mutations curtas.
- Paginação com `useInfiniteQuery` + cursor.

### 8.4 Imagens
- `next/image` sempre; `priority` apenas no LCP.
- WebP/AVIF do CDN.

### 8.5 Métricas
- Web Vitals enviadas ao backend `/v1/metrics/vitals` (sampled 10%).
- Sentry Performance habilitado (10% trace sample em prod).

## 9. Async / Background

- HTTP request **nunca** bloqueia em I/O pesado. Tudo que >300ms vai para Celery.
- Tarefas pesadas: parsing, geração de export LGPD, email em batch, recálculo de snapshots.
- Sem long polling; usar **SSE** ou WebSocket onde precisar de push (apenas SSE no MVP).

## 10. Observação Contínua

- Slow query log do Postgres habilitado para queries >500ms.
- `pg_stat_statements` em prod; review semanal das top 20.
- Dashboard Grafana: p50/p95/p99 por endpoint, query time, parser throughput, cache hit ratio, queue depth Celery.
- Alerta se:
  - p95 de qualquer endpoint sobe >50% vs semana anterior.
  - Cache hit ratio cai <80%.
  - Queue Celery cresce além de 1000 itens sustentado por 5min.
  - DB CPU sustentado >70%.

## 11. Anti-patterns Proibidos

- ❌ `SELECT *` em queries de produção.
- ❌ `for hand in hands: db.execute(...)` (clássico N+1).
- ❌ Cálculo de estatística por hand individual em Python quando dá pra fazer no SQL.
- ❌ String concat de SQL.
- ❌ Cache sem TTL.
- ❌ Cache key sem `env` (cruzamento de ambientes).
- ❌ `time.sleep` em request HTTP.
- ❌ Resposta JSON com objeto aninhado profundo (≥4 níveis) sem paginação.
- ❌ Lib pesada (>50KB gzip) carregada no entry sem `next/dynamic`.
- ❌ Imagem >200KB servida sem `next/image`.
