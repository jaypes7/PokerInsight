# Notas do agente para F1

## Decisoes tomadas
- Implementei a F1 em uma branch unica (`feat/f1-db-001-auth-tables`) para atender ao pedido de fase completa.
- Mantive `F0-DOCS-001` aberto inicialmente por ser opcional, e marquei a F1 como concluida no `TODO.md` apos validar o fluxo integrado.
- Dividi o schema em migrations coesas: auth/auditoria, storage de poker, billing/stats/flags.
- Implementei o parser como pacote puro em `app/parser`, sem dependencia de FastAPI ou SQLAlchemy.
- Usei armazenamento local em `.storage/` com URLs pre-assinadas deterministicas como fallback dev/test.

## Trade-offs
- Auth usa PBKDF2-HMAC local em vez de Argon2id/HIBP por nao adicionar dependencia nova nesta passada; precisa endurecer antes de producao.
- Celery tem fallback local quando a lib nao esta instalada; o contrato da task existe, mas worker real pede adicionar `celery` nas dependencias.
- Storage nao usa boto3/aioboto3 ainda; o wrapper preserva path enforcement e TTL, mas o fluxo MinIO real deve ser conectado depois.
- Golden tests validam invariantes e fixtures anonimizadas, mas ainda nao comparam snapshots JSON canonicos.
- O benchmark e um smoke de throughput, nao uma suite `pytest-benchmark` com baseline estatistico.

## Pontos para revisao humana atenta
- Revisar RLS de tabelas derivadas (`hand_players`, `pots`) por depender de subquery em `hands`.
- Revisar formula de `hero_net_cents`, que hoje usa chips investidos/coletados como aproximaÃ§Ã£o.
- Confirmar se o fallback local de upload via `raw_text` em `/complete` deve permanecer so em dev/test.
- Trocar hashing e email/rate-limit de auth pela implementacao final antes de expor publicamente.

## Comandos executados que tiveram efeito nao-trivial
- `git checkout -b feat/f1-db-001-auth-tables`
- `docker compose -f infra/compose.dev.yml up -d postgres redis`
- `docker compose -f infra/compose.dev.yml down`
- `python -m ruff check . --fix`
- `python -m ruff format .`
- `python -m ruff format --check .`
- `python -m ruff check .`
- `python -m mypy --strict app`
- `python -m pytest tests/unit tests/golden tests/property tests/benchmarks -q`
- `python -m pytest tests/integration -q`


continue as notas a partir daqui, nunca apague notas de outras fases!