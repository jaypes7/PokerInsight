# 08 — Segurança

> Este documento é **normativo**. Toda task que toca rede, banco, auth ou upload deve consultar a seção pertinente antes de codar.

## 1. Modelo de Ameaças (STRIDE resumido)

| Categoria | Ativo / Fluxo | Ameaça concreta | Mitigação principal |
|---|---|---|---|
| **Spoofing** | Login | Credenciais vazadas, brute force | Argon2id, rate limit por IP+email, CAPTCHA após N falhas, MFA opcional (v2) |
| **Tampering** | Upload HH | Cliente envia HH adulterada para inflar stats | Hash SHA-256 do conteúdo armazenado; reparser idempotente; HH é fonte da verdade |
| **Tampering** | JWT | Forjar token | RS256 com chave privada apenas no API; rotação anual; `kid` no header |
| **Repudiation** | Ações sensíveis (delete, billing) | Usuário nega ter feito | `audit_logs` com user_id, IP, user_agent, before/after |
| **Information Disclosure** | Multi-tenant | Usuário A lê hands de B | RLS no Postgres + filtro WHERE user_id em todo repositório; testes de tenant isolation obrigatórios |
| **Information Disclosure** | R2 | URL de objeto vazada | Presigned URLs com expiração ≤15min; objetos com prefixo `users/{user_id}/`; bucket privado |
| **DoS** | Upload | Arquivo gigante / zip-bomb | Limite 50MB por arquivo; 200MB/dia por user free; streaming parser (não carrega tudo em RAM) |
| **DoS** | API | Scraping / abuso | Rate limit por user+IP no Redis (token bucket); WAF na borda (Cloudflare) |
| **Elevation of Privilege** | Admin endpoints | User vira admin | RBAC em coluna `users.role`; nunca confiar em claim do JWT — sempre re-checar no DB para ações admin |

## 2. Autenticação

### 2.1 Senhas
- Hash: **Argon2id**, params `time_cost=3, memory_cost=64MiB, parallelism=4`.
- Mínimo: 10 caracteres, ao menos 1 letra e 1 número (sem regras paranóicas que pioram UX).
- Verificação contra **HaveIBeenPwned** (k-anonymity API) no register e no change-password — bloquear se >0 hits.
- Hash **nunca** é logado nem retornado em endpoint algum.

### 2.2 JWT
- Algoritmo: **RS256**.
- Claims: `sub` (user_id), `iat`, `exp`, `jti`, `role`, `plan`.
- TTL access token: **15 minutos**.
- Chave privada em **Vault/Secrets Manager**; nunca em env var de texto plano em prod.
- Rotação de chaves: anualmente; suportar 2 chaves simultâneas via `kid`.

### 2.3 Refresh tokens (opacos)
- Bytes aleatórios (32B) → base64url; **nunca JWT**.
- Armazenado **hasheado (SHA-256)** em `refresh_tokens` com `expires_at` (30 dias).
- Rotação a cada uso (`/v1/auth/refresh`): o token antigo vira inválido, novo é emitido.
- **Detecção de reuso**: se um refresh token já usado (`revoked_at IS NOT NULL`) for apresentado novamente → revoga **toda a família** (`replaced_by` em cadeia) e força re-login. Log de incidente.
- Cookie: `HttpOnly; Secure; SameSite=Lax; Path=/v1/auth/refresh`.

### 2.4 OAuth (Google)
- Apenas Authorization Code + PKCE; sem implicit flow.
- State (CSRF) gerado server-side e armazenado em Redis com TTL 5min.
- Email do provider precisa estar `verified=true`.

### 2.5 Reset de senha
- Token: 32B aleatórios → hash SHA-256 no DB; TTL 30min; single-use.
- Email não revela se a conta existe (mesma resposta para email cadastrado ou não).

## 3. Autorização

- Modelo: **RBAC simples** — `user`, `admin`. Sem grupos/orgs no MVP.
- Toda query SQL passa por repositório que aceita `user_id` explicitamente. **Proibido** passar `user_id` vindo do path/query — sempre do JWT.
- RLS habilitado em tabelas multi-tenant (ver `04-DATA-MODEL.md`).
- Admin endpoints (`/v1/admin/*`) checam `role=='admin'` **lendo do DB**, não do JWT (defesa em profundidade).
- Impersonação por admin: requer reason text, gera linha em `audit_logs` com `action='admin.impersonate'`.

## 4. Criptografia

- **Em trânsito**: TLS 1.3 obrigatório; HSTS `max-age=31536000; includeSubDomains; preload`.
- **Em repouso**:
  - Postgres: encryption at rest do provedor (RDS/Neon/Supabase).
  - R2: encryption padrão Cloudflare.
  - Backups: criptografados antes de sair do provedor.
- **Em uso (campos sensíveis)**: emails são armazenados em texto plano (precisamos buscar por eles); CPF nunca é coletado no MVP.

## 5. Segurança de Upload

- Tamanho: **50MB** por arquivo (hard limit no presigned policy e no API).
- Quota diária por user free: **200MB**; pro: **2GB**.
- Content-type aceito: `text/plain`; rejeitar binário detectado por magic bytes.
- **Validação de conteúdo**:
  1. Detectar encoding (`chardet`); aceitar utf-8 (com/sem BOM), cp1252, iso-8859-1.
  2. Primeira linha deve casar regex `^(PokerStars|POKERSTARS)`.
  3. Se >10MB, é provavelmente bundle de muitas sessões — OK; se header inválido, rejeita.
- Sem execução de qualquer conteúdo do arquivo. Parser puro-Python, sem `eval`/`exec`.
- Vírus scan: ClamAV opcional v2; no MVP, a estrutura do parser já bloqueia conteúdo arbitrário (só lemos linhas que casam regex).

## 6. Rate Limiting

| Endpoint | Limite | Janela | Escopo |
|---|---|---|---|
| `POST /v1/auth/login` | 5 | 1 min | IP+email |
| `POST /v1/auth/register` | 3 | 10 min | IP |
| `POST /v1/auth/forgot-password` | 3 | 10 min | IP+email |
| `POST /v1/imports` | 60 | 1 hora | user |
| `GET /v1/hands` | 600 | 1 min | user |
| `GET /v1/stats` | 60 | 1 min | user |
| Catch-all autenticado | 600 | 1 min | user |
| Catch-all anônimo | 60 | 1 min | IP |

Implementação: `slowapi` + Redis (token bucket). Headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`.

## 7. Validação de Entrada

- Toda entrada passa por **Pydantic v2** (`BaseModel` com `model_config = ConfigDict(extra='forbid')`).
- IDs em path/query: validados como `UUID` antes de chegar no repositório.
- Strings: `min_length`/`max_length` explícitos; `pattern` quando aplicável.
- Nunca interpolar string em SQL — **somente** SQLAlchemy core/ORM com bind params.
- HTML/JSON em respostas: serializado por libs (orjson), nunca concatenado.

## 8. Headers de Segurança (frontend)

```
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline' https://js.stripe.com; img-src 'self' data: https:; connect-src 'self' https://api.pokerinsight.app https://api.stripe.com; frame-src https://js.stripe.com
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=()
```

Configurado em `next.config.js` via `headers()` e double-checked no edge (Cloudflare).

CORS: `Access-Control-Allow-Origin` apenas `https://app.pokerinsight.app` (e localhost em dev); `Allow-Credentials: true`; lista explícita de métodos.

## 9. Secrets Management

- **Dev**: `.env.local` no gitignore; `.env.example` versionado com placeholders.
- **CI**: GitHub Actions secrets; nunca printar em log.
- **Staging/Prod**: Vault, Doppler ou Secrets Manager do provedor; injetados como env vars em runtime.
- Proibido: secrets em código, em PR, em issue, em arquivo de teste.
- **Pre-commit hook** com `gitleaks` ou `trufflehog` para detectar leaks.
- Rotação: chaves de assinatura JWT a cada 12 meses; senhas de DB a cada 6; chaves de R2 a cada 12; tokens de webhook Stripe revisados ao trocar de ambiente.

## 10. Logs e Auditoria

- Logs estruturados (JSON) com `structlog`.
- **Nunca** logar: senha (mesmo hash), token JWT inteiro (logar apenas `jti`), refresh token, body de webhook contendo PAN (usar `**REDACTED**`).
- Logar: user_id, request_id (UUID gerado no middleware), path, status, latency_ms, IP (hash quando GDPR/LGPD aplicável), user_agent truncado.
- `audit_logs` table: ações sensíveis (login, password change, plan change, account delete, admin impersonate, data export).
- Retenção: logs operacionais 90 dias; `audit_logs` 5 anos.

## 11. LGPD Compliance

### 11.1 Bases legais
- **Execução de contrato**: dados de conta, billing, hands processadas.
- **Legítimo interesse**: logs de segurança, auditoria.
- **Consentimento**: cookies analíticos (banner), marketing emails.

### 11.2 Direitos do titular
- **Acesso/Portabilidade**: `POST /v1/users/me/export` → gera ZIP em até 15 dias com JSON de todos os dados + raw HH files. Notifica por email.
- **Eliminação**: `DELETE /v1/users/me` → soft delete imediato + hard delete em 30 dias (grace period); subscription cancelada; HH files removidos do R2; `audit_logs` mantidos (anonimizados, base legal: legítimo interesse / obrigação legal).
- **Retificação**: `PATCH /v1/users/me`.
- **Oposição**: settings para desativar emails de marketing; cookies analíticos desligáveis.

### 11.3 DPO e contato
- Endereço de contato: `dpo@pokerinsight.app`.
- Página pública `/privacidade` com política em PT-BR.
- Página pública `/termos`.

### 11.4 Sub-processadores
Listados publicamente em `/sub-processadores`. MVP:
- Cloudflare (CDN, R2)
- Stripe (pagamentos)
- Resend (email transacional)
- Provedor de DB (Neon/Supabase/RDS)
- Sentry (errors), Grafana Cloud (metrics)

### 11.5 Transferência internacional
- Cloudflare, Stripe, Resend são US. Justificativa: garantias contratuais (DPA) + cláusulas-padrão. Documentar no RoPA (Record of Processing Activities) interno.

## 12. OWASP Top 10 — Mapeamento

| OWASP | Mitigação |
|---|---|
| A01 Broken Access Control | RLS + repositórios com user_id explícito + testes de tenant isolation |
| A02 Cryptographic Failures | TLS 1.3, Argon2id, RS256, secrets nunca em código |
| A03 Injection | SQLAlchemy parametrizado, Pydantic, nenhuma concat de SQL |
| A04 Insecure Design | Threat model documentado; review obrigatório em PRs que tocam auth/billing |
| A05 Security Misconfiguration | Headers de segurança em CI (teste); Docker images sem root; mypy --strict |
| A06 Vulnerable Components | `pip-audit` + `npm audit` em CI; Dependabot semanal |
| A07 Identification & Auth Failures | Rate limit em login, Argon2id, refresh rotation com reuse detection |
| A08 Software & Data Integrity Failures | SRI em scripts externos; image pinning (`@sha256:...`); webhook Stripe verifica assinatura |
| A09 Logging & Monitoring Failures | structlog + Sentry + alertas Grafana; SLOs definidos |
| A10 SSRF | Apenas R2 SDK para acesso externo; sem fetch de URLs vindas de input do user no MVP |

## 13. Webhook de Provedores

- **Stripe**: verificar assinatura com `Stripe-Signature`; tolerância 5min; `webhook_events.event_id` UNIQUE para idempotência; reprocessar de forma idempotente.
- **Resend** (bounces/complaints): assinatura HMAC; atualiza `users.email_verified=false` em hard bounce.

## 14. Política de Divulgação de Vulnerabilidades

- `security.txt` em `/.well-known/security.txt`.
- Email: `security@pokerinsight.app`.
- Reconhecimento público em página `/security/hall-of-fame` (com consentimento).
- SLA inicial: triagem em 5 dias úteis.

## 15. Checklists de Code Review (sensível)

Em qualquer PR que altera autenticação, autorização, billing, upload ou queries multi-tenant, o reviewer **precisa** confirmar:

- [ ] `user_id` vem do JWT, não do client.
- [ ] Toda query nova tem teste de tenant isolation.
- [ ] Sem string interpolation em SQL.
- [ ] Logs novos não vazam PII/segredo.
- [ ] Mudança em rate limit foi discutida.
- [ ] Mudança em escopo de cookie/JWT foi discutida.
- [ ] Alteração em política RLS tem migration + teste.
