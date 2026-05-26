# AGENTS.md — Protocolo para Codex & Claude Code

> Este arquivo segue a convenção `AGENTS.md` reconhecida nativamente por **OpenAI Codex** e **Anthropic Claude Code**. Tudo que está aqui é regra obrigatória para qualquer agente de IA contribuindo neste repositório.
>
> Em caso de conflito entre uma instrução do usuário humano em chat e este arquivo, **siga a do usuário humano** — mas pergunte se ele quer que a regra deste arquivo seja atualizada.

---

## 1. Identidade dos agentes

Este projeto é desenvolvido por dois agentes de IA, geralmente alternando:

- **Codex (OpenAI)** — bom em scaffolding, refactors largos e tarefas que pedem geração de muitos arquivos
- **Claude Code (Anthropic)** — bom em raciocínio profundo, depuração, especificações sutis (ex.: parser do HH, regras de stats)

Use o melhor agente para cada tipo de tarefa; a TODO list indica sugestões em algumas tasks (`💡 sugestão: Claude Code` ou `💡 sugestão: Codex`).

---

## 2. Antes de começar qualquer tarefa

1. Leia o `README.md` (overview rápido).
2. Leia este `AGENTS.md` por completo.
3. Abra `TODO.md` e localize a task pelo seu **TASK ID** (ex.: `F1-PARSER-003`).
4. Leia os documentos referenciados no campo "Docs" da task.
5. Se algo estiver ambíguo, **pare e pergunte ao humano** antes de inventar comportamento.

---

## 3. Workflow Git

### 3.1 Branches

- `main` — protegida, só recebe via PR aprovado
- `develop` — branch de integração (opcional; pode ser direto em main para projetos pequenos)
- Para cada task, crie branch: `<tipo>/<task-id>-<slug-curto>`
  - tipos: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `ci`, `build`
  - exemplo: `feat/f1-parser-003-pokerstars-header`

### 3.2 Commits

Padrão **Conventional Commits**:
```
<tipo>(<escopo>): <descrição curta no imperativo, minúsculo>

<corpo opcional explicando o porquê>

Refs: <TASK-ID>
```

Exemplos:
```
feat(parser): adiciona tokenizer para header de mão PokerStars PT-BR

Refs: F1-PARSER-003
```

```
fix(stats): corrige denominador de VPIP em mãos walked

Walked hands (BB ganha sem ninguém limpar) não devem contar para VPIP
do BB porque ele não teve oportunidade voluntária de colocar fichas.

Refs: F2-STATS-007
```

Regras:
- Um commit por intenção lógica (não misturar feat com refactor não relacionado)
- Sempre incluir `Refs: <TASK-ID>` no rodapé
- Nunca commitar arquivo gerado, segredo, ou `*.env` (vide `.gitignore`)
- Nunca commitar HH real de jogadores — só fixtures anonimizadas em `packages/hh-fixtures/`

### 3.3 Pull Request

Template obrigatório:
```markdown
## Task
- ID: <TASK-ID>
- Link: <link na TODO.md>

## O que foi feito
- bullets curtos

## Como testar
1. ...

## Checklist
- [ ] Todos os testes passam localmente (`make test`)
- [ ] Lint OK (`make lint`)
- [ ] Coverage não caiu (`make coverage`)
- [ ] Atualizei a documentação relevante
- [ ] Atualizei a TODO.md marcando a task como concluída
- [ ] Não há segredos no diff
- [ ] Não há TODO/FIXME novos sem issue criada

## Notas para o revisor humano
- ...

## Screenshots (se UI)
- ...
```

PRs sem o checklist preenchido são bloqueados.

---

## 4. Definição de pronto (DoD)

Uma task só é "pronta" quando:

1. ✅ Código implementado conforme o spec
2. ✅ **Testes unitários** com >85% coverage no código novo (alvo global: 80%)
3. ✅ **Testes de integração** quando há I/O (DB, S3, HTTP externo)
4. ✅ Lint, type-check e format passando
5. ✅ Documentação atualizada (docstrings + arquivo em `docs/` quando aplicável)
6. ✅ PR aprovado por humano (ou outro agente quando autorizado)
7. ✅ CI verde (todas as checks)
8. ✅ Sem regressão em benchmarks de performance (parser e stats)
9. ✅ Item correspondente marcado `[x]` em `TODO.md`

---

## 5. Estrutura do código (regras invioláveis)

### 5.1 Backend Python

- **Tipagem estrita**: nada de `Any` sem comentário justificando. `mypy --strict`.
- **Pydantic v2** para todos os DTOs de borda (request/response e parsing).
- **Dependency Injection** via `Depends` do FastAPI. Sem singletons globais.
- **Repository pattern** para acesso ao banco: `pokerinsight.db.repositories.*`.
- **Casos de uso** ficam em `pokerinsight.services.*` e nunca importam FastAPI.
- **Routers** finos: validação Pydantic → chamar service → retornar response model.
- **Async first**: rotas, repositórios e Celery tasks usam `async/await`. Funções de cálculo puro podem ser sync.
- **Sem `print`** — use `structlog`.
- **Sem `datetime.utcnow()`** — use `datetime.now(timezone.utc)`.
- **Sem `os.getenv` direto** — passe pela classe de settings (`pokerinsight.core.config.Settings`).

### 5.2 Frontend TypeScript

- `strict: true` no `tsconfig.json`. Sem `any` implícito.
- Server Components por padrão; `'use client'` só quando precisar.
- Estado de servidor → **TanStack Query**. Estado UI local → useState/useReducer. Estado global mínimo → Zustand.
- Componentes UI primitivos vêm de **shadcn/ui**. Não recriar botões/inputs do zero.
- Acessibilidade: todo input precisa de `<label>`, todo botão de `aria-label` se for icon-only, foco visível.
- i18n: textos da UI passam por `next-intl` (PT-BR primário, EN secundário).

### 5.3 Convenções gerais

- Nomes em **inglês** no código (variáveis, funções, classes, tabelas).
- Strings de UI e mensagens de erro voltadas ao usuário em **PT-BR** (via i18n).
- Logs e exceções internas em **inglês** (para padronizar com bibliotecas).
- Comentários: prefira código autoexplicativo. Comentários explicam **por quê**, não **o quê**.

---

## 6. Segurança — proibições absolutas

❌ **Nunca** commitar:
- API keys, tokens, certificados, `.env*`
- HH reais de jogadores (privacidade)
- Dumps de banco
- Conteúdo de e-mails de usuários

❌ **Nunca** desabilitar:
- Validação Pydantic em rotas
- Checks de tenant (toda query filtrada por `user_id` ou `account_id`)
- Rate limiting
- HTTPS em ambientes não-dev

❌ **Nunca** introduzir:
- SQL string interpolation (`f"SELECT * FROM x WHERE y={user_input}"`) — sempre usar parâmetros do ORM
- `subprocess.shell=True` com input externo
- `eval`, `exec`, `pickle.loads` com input externo
- Dependência sem revisão (verifique no `requirements.lock` / `pnpm-lock.yaml`)

Veja `docs/08-SECURITY.md` para o modelo de ameaças completo.

---

## 7. Performance — proibições e práticas

❌ **N+1 queries**: ao iterar uma lista de objetos, nunca faça query por item. Use `selectinload`, `joinedload`, `IN ()`, ou JOINs.
❌ **Loops em Python sobre milhares de mãos**: prefira operações vetorizadas (pandas/SQL).
❌ **Cálculos de stats em request síncrona**: jogos com >1k mãos vão para Celery.
✅ **Cache** todo cálculo agregado caro (Redis com TTL e invalidação por evento).
✅ **Batch insert** ao persistir mãos: nunca um `INSERT` por mão.
✅ **EXPLAIN ANALYZE** toda query nova que toque `hands` ou `actions`.

Detalhes: `docs/10-PERFORMANCE.md`.

---

## 8. Testes — protocolo do agente

Antes de marcar uma task como concluída:

```bash
make test        # roda tudo
make lint        # ruff + mypy + biome
make test-unit   # só unit, rápido
make test-int    # integração (precisa docker compose up postgres redis)
make coverage    # gera relatório
```

Regras:
- Para qualquer função no parser ou no módulo de stats, criar **golden tests** com pelo menos 5 mãos representativas em `apps/api/tests/golden/`.
- Para rotas, escreva 1 teste de happy path + 1 de validação + 1 de autorização (tenant errado).
- Para correções de bug, escreva primeiro o teste que reproduz o bug, depois corrija.
- Mocks de I/O externo: usar `respx` (HTTPX) e `aiosmtpd` (e-mail). Não mockar nosso próprio código sem necessidade.

Detalhes: `docs/09-TESTING-CICD.md`.

---

## 9. Limites do agente — quando parar e perguntar

Pare e peça orientação humana se:

- A task requer decisão de produto não documentada (ex.: "qual deve ser o preço do plano Pro?").
- A spec do parser não cobre um token visto no arquivo de input — **nunca invente** o significado.
- Você precisaria modificar o schema do banco em produção sem migração reversível.
- O teste exposto é frágil e você está tentado a torná-lo mais permissivo só para passar.
- Você quer adicionar uma dependência nova com >5k LOC ou licença incompatível.
- Você detecta um conflito entre dois documentos (ex.: PRD diz X, API spec diz Y).
- Você precisa acessar credenciais ou dados reais de produção.

---

## 10. Logs do trabalho do agente

Toda branch do agente deve manter um arquivo `AGENT_NOTES.md` na raiz da branch com:

```markdown
# Notas do agente para <TASK-ID>

## Decisões tomadas
- ...

## Trade-offs
- ...

## Pontos para revisão humana atenta
- ...

## Comandos executados que tiveram efeito não-trivial
- ...
```

Este arquivo é apagado quando o PR é merged (vira parte da descrição do PR).

---

## 11. Ferramentas e atalhos

`Makefile` na raiz com targets padronizados:

```
make help            # lista targets
make setup           # instala dependências do monorepo
make dev             # docker compose up + servidores
make test            # todos os testes
make test-unit
make test-int
make lint            # ruff + mypy + biome + prettier
make format          # autoformat
make coverage
make migrate         # alembic upgrade head
make migrate-new MSG="add hands table"
make seed            # carrega fixtures
make parse-fixture FILE=packages/hh-fixtures/sample.txt
make bench-parser    # benchmark do parser
make explain QUERY="..."  # EXPLAIN ANALYZE da query
make clean
```

Use sempre o `Makefile` em vez de invocar comandos diretamente, para evitar drift de flags.

---

## 12. Comunicação com o humano (resumos de PR e tasks)

- Seja **conciso**. Bullets curtos, não parágrafos.
- Sempre referencie a `TASK-ID`.
- Sinalize riscos explicitamente (`⚠️ Risco:`).
- Use português brasileiro para o humano; inglês para código/commits/PRs.
- Se o trabalho gerou follow-ups, adicione-os à TODO.md como tasks novas com prefixo `F?-FOLLOWUP-NNN`.

---

## 13. O que NÃO está no escopo deste arquivo

- Diretrizes de produto → `docs/01-PRD.md`
- Decisões de arquitetura → `docs/02-ARCHITECTURE.md`
- Stack e versões → `docs/03-TECH-STACK.md`
- Lista de tasks → `TODO.md`

---

**Última atualização**: criação inicial. Atualize via PR quando regras evoluírem.
