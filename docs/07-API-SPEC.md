# 07 — Especificação de API REST

> Base URL prod: `https://api.pokerinsight.app/v1`
> OpenAPI/Swagger ao vivo: `/docs` (Swagger UI) e `/redoc`. Todo endpoint **DEVE** ter docstring + response models tipados.

---

## 1. Convenções globais

- **Versionamento**: prefixo `/v1`. Quebras vão para `/v2`.
- **Formato**: JSON (`application/json; charset=utf-8`).
- **Datas**: ISO 8601 UTC com `Z`. Ex: `"2026-05-15T19:01:22Z"`.
- **Dinheiro**: sempre objeto `{ "amount": 1990, "currency": "USD" }` em **centavos** (BIGINT). Nunca string formatada.
- **Paginação**: cursor-based em coleções grandes.
  - Request: `?limit=50&after=<opaque>`
  - Response: `{ "data": [...], "page": { "next_after": "...", "has_more": true } }`
- **Erros**: RFC 7807 (Problem Details).

  ```json
  {
    "type": "https://errors.pokerinsight.app/validation",
    "title": "Validation Error",
    "status": 422,
    "detail": "Invalid file size",
    "instance": "/v1/imports",
    "errors": [
      { "field": "file", "code": "TOO_LARGE", "message": "max 50MB on free plan" }
    ],
    "trace_id": "01HX..."
  }
  ```

- **Idempotência**: POST que cria recurso aceita header `Idempotency-Key: <uuid>`. Repetições retornam mesmo `id`.
- **Rate limit**: por usuário e por IP. Headers de resposta:
  - `X-RateLimit-Limit`
  - `X-RateLimit-Remaining`
  - `X-RateLimit-Reset` (epoch s)
- **Tracing**: header `X-Request-ID` (gerado se ausente); ecoa em response.
- **CORS**: lista de origens em allow-list (configurável).

### 1.1 Códigos HTTP esperados

| Código | Uso |
|--------|-----|
| 200 | OK genérico |
| 201 | Criado |
| 202 | Aceito (processo assíncrono) |
| 204 | Sem corpo (DELETE) |
| 304 | ETag bate |
| 400 | Bad request (JSON malformado) |
| 401 | Não autenticado |
| 403 | Autenticado mas sem permissão |
| 404 | Não encontrado |
| 409 | Conflito (recurso já existe) |
| 415 | Media type não suportado |
| 422 | Validação falhou (Pydantic) |
| 429 | Rate limit |
| 500 | Erro interno (sentry alertado) |
| 503 | Manutenção / dependência fora |

---

## 2. Autenticação

### 2.1 Modelo

- **Access token** (JWT RS256, TTL 15min) em cookie `httpOnly`, `Secure`, `SameSite=Lax`, name `pi_access`.
- **Refresh token** (opaco, 64 bytes hex) em cookie `httpOnly` `Secure` `SameSite=Lax` `Path=/v1/auth/refresh`, name `pi_refresh`.
- Em ambientes API-only (mobile), aceitar `Authorization: Bearer <access>`.

### 2.2 Endpoints de auth

#### `POST /v1/auth/register`

```http
POST /v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "MinhaSenh@12",
  "display_name": "João",
  "locale": "pt-BR",
  "accept_terms": true,
  "captcha_token": "..."
}
```

**Respostas**:
- `201` — `{ "user_id": "uuid", "email_verification_required": true }`
- `409` — e-mail já em uso
- `422` — senha fraca / e-mail inválido

#### `POST /v1/auth/login`

```json
{ "email": "...", "password": "...", "captcha_token": "..." }
```

`200` define cookies; corpo: `{ "user": { "id": "...", "email": "...", "display_name": "...", "plan": "free" } }`.

`401` se credencial errada. `423` se conta bloqueada por brute-force.

#### `POST /v1/auth/refresh`

Lê cookie refresh, rotaciona, retorna novo par. `401` se reuse detectado (e revoga toda a família).

#### `POST /v1/auth/logout`

Revoga refresh atual; limpa cookies.

#### `POST /v1/auth/verify-email`

Body: `{ "token": "..." }`. `200` em sucesso.

#### `POST /v1/auth/forgot-password`

Body: `{ "email": "..." }`. Sempre `204` (não revela se existe).

#### `POST /v1/auth/reset-password`

Body: `{ "token": "...", "new_password": "..." }`. `200` em sucesso.

#### `GET /v1/auth/oauth/google/start`

Redirect 302 para Google.

#### `GET /v1/auth/oauth/google/callback`

Recebe `code`, valida, cria/atualiza usuário, define cookies, redireciona para `/dashboard`.

---

## 3. Endpoints `/v1/users/me`

#### `GET /v1/users/me`

```json
{
  "id": "...",
  "email": "...",
  "display_name": "...",
  "locale": "pt-BR",
  "timezone": "America/Sao_Paulo",
  "plan": "pro",
  "subscription": {
    "status": "active",
    "current_period_end": "2026-06-15T00:00:00Z",
    "cancel_at_period_end": false
  },
  "quotas": {
    "hands_this_period": 1234,
    "hands_quota": 5000,
    "period_resets_at": "2026-06-15T00:00:00Z"
  },
  "created_at": "..."
}
```

#### `PATCH /v1/users/me`

```json
{ "display_name": "...", "timezone": "...", "locale": "..." }
```

#### `POST /v1/users/me/change-password`

```json
{ "current_password": "...", "new_password": "..." }
```

#### `POST /v1/users/me/export`

Inicia job de exportação LGPD. Retorna `202` com `export_id`. Resultado fica em `/v1/users/me/exports/:id`.

#### `DELETE /v1/users/me`

```json
{ "confirmation": "DELETAR", "password": "..." }
```

Soft delete imediato + agendamento de purga em 30 dias. `204`.

---

## 4. Imports

#### `POST /v1/imports`

Inicia upload. Retorna URL pre-assinada.

Request:
```json
{ "filename": "session_2026-05-15.txt", "size_bytes": 234567, "sha256": "ab..." }
```

Response 201:
```json
{
  "import_id": "uuid",
  "upload_url": "https://r2.../pi-hh-raw/<key>?X-Amz-...=...",
  "upload_method": "PUT",
  "expires_at": "2026-05-15T19:15:00Z",
  "max_size_bytes": 52428800
}
```

#### `POST /v1/imports/:id/complete`

Sinaliza que o upload terminou. API enfileira parsing. Retorna `202` com `{ "status": "processing" }`.

#### `GET /v1/imports/:id`

```json
{
  "id": "...",
  "status": "succeeded",
  "original_filename": "...",
  "total_hands_detected": 250,
  "total_hands_imported": 248,
  "total_hands_duplicate": 1,
  "total_errors": 1,
  "started_at": "...",
  "finished_at": "...",
  "errors_url": "/v1/imports/:id/errors"
}
```

#### `GET /v1/imports/:id/errors?limit=20&after=`

Lista os erros do import.

#### `GET /v1/imports`

Listagem do usuário. Filtros: `?status=...&from=...&to=...`.

#### `GET /v1/imports/:id/events`

**SSE** (`text/event-stream`) para acompanhar progresso. Eventos:
```
event: status
data: {"status":"processing","percent":42}

event: status
data: {"status":"succeeded","summary":{...}}
```

---

## 5. Hands

#### `GET /v1/hands`

Filtros:
- `from`, `to` (datas)
- `tournament_id`
- `position` (BTN,CO,...)
- `min_buyin`, `max_buyin`
- `game_type`
- `table_max_players`
- `won` (true/false)
- `order` (`played_at_desc`, `pot_desc`)

Cursor pagination. Default limit 50, max 200.

Response item (resumo):
```json
{
  "id": "...",
  "site_hand_id": "260820828710",
  "played_at": "2026-05-15T23:01:22Z",
  "game_type": "tournament",
  "table_max_players": 9,
  "level_name": "I",
  "blinds": { "sb": 10, "bb": 20, "ante": 0 },
  "hero_position": "BB",
  "hero_hole_cards": ["Td","Jc"],
  "board": ["8h","Qh","Ad"],
  "hero_net_cents": -20,
  "currency": "USD",
  "pot_total": 140,
  "went_to_showdown": false
}
```

#### `GET /v1/hands/:id`

Detalhe completo: seats, todas as ações, pots, hero_summary.

#### `GET /v1/hands/:id/raw`

Retorna o texto original (`text/plain`) — útil para depuração e para o replayer.

---

## 6. Stats

#### `GET /v1/stats`

Query params (mesmos filtros de `/v1/hands`):

```json
{
  "scope": {
    "from": "2026-04-01T00:00:00Z",
    "to": "2026-05-15T23:59:59Z",
    "game_type": "tournament"
  },
  "sample_hands": 12345,
  "metrics": {
    "vpip": 23.4,
    "pfr": 18.2,
    "three_bet": 5.6,
    "fold_to_three_bet": 62.1,
    "af": 2.1,
    "wtsd": 27.4,
    "wsd": 51.3
  },
  "by_position": {
    "BTN": { "sample_hands": 1234, "vpip": 38.1, ... },
    "CO":  { ... }
  },
  "computed_at": "...",
  "from_cache": true
}
```

Cache: 1h, invalidado por import. Header `Cache-Control: private, max-age=60`.

#### `GET /v1/stats/bankroll`

Para torneios. Response:
```json
{
  "scope": { ... },
  "currency": "USD",
  "series": [
    { "date": "2026-05-01", "cumulative_profit_cents": 0, "tournaments_played": 0 },
    { "date": "2026-05-02", "cumulative_profit_cents": -350, "tournaments_played": 3 },
    { "date": "2026-05-15", "cumulative_profit_cents": 12500, "tournaments_played": 18 }
  ],
  "summary": {
    "total_buyins_cents": 84000,
    "total_payouts_cents": 96500,
    "net_cents": 12500,
    "roi_percent": 14.9,
    "itm_percent": 22.2,
    "tournaments_played": 18
  }
}
```

---

## 7. Billing

#### `GET /v1/billing/plans`

```json
{
  "plans": [
    { "id": "free", "name": "Free", "hands_quota_30d": 5000, "price_cents": 0 },
    { "id": "pro",  "name": "Pro",  "hands_quota_30d": null,
      "price_cents": 1990, "currency": "BRL", "stripe_price_id": "price_..." }
  ]
}
```

#### `POST /v1/billing/checkout`

```json
{ "plan_id": "pro", "success_url": "...", "cancel_url": "..." }
```

Retorna `{ "checkout_url": "https://checkout.stripe.com/..." }`.

#### `POST /v1/billing/portal`

Retorna URL do Stripe Customer Portal.

#### `POST /v1/webhooks/stripe`

Endpoint público, valida HMAC `Stripe-Signature`. Idempotente via `event.id`.

---

## 8. Admin (RBAC `role=admin`)

- `GET /v1/admin/users?email=...` — busca
- `GET /v1/admin/users/:id`
- `POST /v1/admin/users/:id/impersonate` — gera sessão temporária (auditada). **Só com flag explícita.**
- `GET /v1/admin/imports?status=failed` — diagnóstico
- `POST /v1/admin/imports/:id/reparse` — força reparse

---

## 9. Health

- `GET /healthz` → `200 OK` se app sobe.
- `GET /readyz` → checa DB+Redis; `503` se falha.
- `GET /version` → `{ "version": "1.2.3", "commit": "abc123" }`.

---

## 10. Schemas Pydantic (referência sintética)

```python
class MoneyDTO(BaseModel):
    amount: int = Field(..., ge=0)
    currency: Literal["USD","BRL"]


class HandSummaryDTO(BaseModel):
    id: UUID
    site_hand_id: str
    played_at: AwareDatetime
    game_type: Literal["tournament","cash"]
    table_max_players: int
    level_name: str | None
    blinds: BlindsDTO
    hero_position: str | None
    hero_hole_cards: list[Card] | None
    board: list[Card] = []
    hero_net_cents: int
    currency: Literal["USD","BRL"]
    pot_total: int
    went_to_showdown: bool


class HandDetailDTO(HandSummaryDTO):
    seats: list[SeatDTO]
    actions: list[ActionDTO]
    pots: list[PotDTO]
    site_table_name: str
    button_seat: int
    raw_text_url: HttpUrl
```

---

## 11. Documentação automática

- Swagger UI em `/docs` (não público em prod sem auth basic).
- ReDoc em `/redoc`.
- Spec OpenAPI exportado para `apps/api/openapi.json` em CI; usado pelo frontend para gerar tipos com `openapi-typescript`.
