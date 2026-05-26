# Executar F0 Foundation

> Leia o [TODO.md](TODO.md) e realize as tarefas da fase F0 - Foundation

<details><summary>35 previous messages</summary>

> Vou começar pela base do protocolo: ler o README e o TODO para mapear exatamente quais itens estão na F0, depois sigo pelos docs referenciados antes de tocar em arquivos.
>
> A F0 é um bloco grande, então vou tratar como uma entrega única de foundation em branch própria e preservar os arquivos já existentes. O status mostra vários arquivos ainda não versionados; vou inspecionar a árvore antes de decidir o que criar ou complementar.
>
> Branch criada para a fase toda. Agora vou ler os trechos de arquitetura, segurança, data model, performance e observabilidade que definem compose, API, Alembic, headers e logging.
>
> Já tenho a superfície da F0: monorepo/tooling, compose, CI, API, Alembic, web e templates GitHub. Vou criar os scaffolds agora, mantendo o código enxuto para que lint/test tenham algo real para validar em vez de só arquivos vazios.
>
> <details><summary>Created 15 files</summary>
>
> - Wrote `./.editorconfig` (+15 -0)
> - Wrote `./.env.example` (+56 -0)
> - Wrote `./.gitattributes` (+8 -0)
> - Wrote `./.gitignore` (+51 -0)
> - Wrote `./.husky/commit-msg` (+1 -0)
> - Wrote `./.husky/pre-commit` (+1 -0)
> - Wrote `./.husky/pre-push` (+2 -0)
> - Wrote `./.nvmrc` (+1 -0)
> - Wrote `./.python-version` (+1 -0)
> - Wrote `./AGENT_NOTES.md` (+18 -0)
> - Wrote `./CHANGELOG.md` (+11 -0)
> - Wrote `./LICENSE` (+7 -0)
> - Wrote `./commitlint.config.cjs` (+6 -0)
> - Wrote `./package.json` (+35 -0)
> - Wrote `./pnpm-workspace.yaml` (+3 -0)
>
> </details>
>
> A primeira camada do repo está no lugar: workspace, hooks, env example, changelog e notas do agente. Agora vou adicionar a API FastAPI com config, logging, DB async, Alembic e testes mínimos.
>
> <details><summary>Created 20 files</summary>
>
> - Wrote `./apps/api/alembic.ini` (+39 -0)
> - Wrote `./apps/api/alembic/env.py` (+62 -0)
> - Wrote `./apps/api/alembic/script.py.mako` (+25 -0)
> - Wrote `./apps/api/alembic/versions/202605260001_initial_empty.py` (+20 -0)
> - Wrote `./apps/api/app/__init__.py` (+3 -0)
> - Wrote `./apps/api/app/core/__init__.py` (+1 -0)
> - Wrote `./apps/api/app/core/config.py` (+75 -0)
> - Wrote `./apps/api/app/db/__init__.py` (+1 -0)
> - Wrote `./apps/api/app/db/base.py` (+15 -0)
> - Wrote `./apps/api/app/db/session.py` (+26 -0)
> - Wrote `./apps/api/app/main.py` (+109 -0)
> - Wrote `./apps/api/app/observability/__init__.py` (+1 -0)
> - Wrote `./apps/api/app/observability/logging.py` (+41 -0)
> - Wrote `./apps/api/pyproject.toml` (+50 -0)
> - Wrote `./apps/api/requirements-dev.txt` (+8 -0)
> - Wrote `./apps/api/requirements.txt` (+9 -0)
> - Wrote `./apps/api/tests/conftest.py` (+5 -0)
> - Wrote `./apps/api/tests/integration/test_db.py` (+12 -0)
> - Wrote `./apps/api/tests/unit/test_health.py` (+22 -0)
> - Wrote `./apps/api/tests/unit/test_logging.py` (+12 -0)
>
> </details>
>
> O backend agora tem endpoints, settings, logging estruturado, sessão async e Alembic reversível. Vou completar a camada de infra e GitHub: compose dev/CI, templates, CODEOWNERS, SECURITY e workflow CI.
>
> <details><summary>Created 13 files</summary>
>
> - Wrote `./.github/CODEOWNERS` (+4 -0)
> - Wrote `./.github/ISSUE_TEMPLATE/bug_report.yml` (+25 -0)
> - Wrote `./.github/ISSUE_TEMPLATE/feature_request.yml` (+22 -0)
> - Wrote `./.github/ISSUE_TEMPLATE/security.yml` (+14 -0)
> - Wrote `./.github/PULL_REQUEST_TEMPLATE.md` (+24 -0)
> - Wrote `./.github/workflows/ci.yml` (+141 -0)
> - Wrote `./CONTRIBUTING.md` (+15 -0)
> - Wrote `./SECURITY.md` (+22 -0)
> - Wrote `./apps/api/Dockerfile` (+20 -0)
> - Wrote `./infra/compose.ci.yml` (+68 -0)
> - Wrote `./infra/compose.dev.yml` (+63 -0)
> - Wrote `./infra/minio/create-buckets.sh` (+6 -0)
> - Wrote `./infra/postgres/init/001_extensions.sql` (+3 -0)
>
> </details>
>
> Infra e templates estão criados. Falta a parte web e depois eu rodo instalação/lint/test para deixar as arestas aparecerem de verdade.
>
> <details><summary>Created 23 files</summary>
>
> - Wrote `./apps/web/Dockerfile` (+22 -0)
> - Wrote `./apps/web/components.json` (+19 -0)
> - Wrote `./apps/web/eslint.config.mjs` (+3 -0)
> - Wrote `./apps/web/next-env.d.ts` (+4 -0)
> - Wrote `./apps/web/next.config.ts` (+35 -0)
> - Wrote `./apps/web/package.json` (+49 -0)
> - Wrote `./apps/web/playwright.config.ts` (+20 -0)
> - Wrote `./apps/web/postcss.config.mjs` (+7 -0)
> - Wrote `./apps/web/prettier.config.mjs` (+7 -0)
> - Wrote `./apps/web/public/.gitkeep` (+1 -0)
> - Wrote `./apps/web/src/app/globals.css` (+39 -0)
> - Wrote `./apps/web/src/app/layout.tsx` (+19 -0)
> - Wrote `./apps/web/src/app/page.tsx` (+44 -0)
> - Wrote `./apps/web/src/components/ui/button.tsx` (+18 -0)
> - Wrote `./apps/web/src/lib/utils.ts` (+6 -0)
> - Wrote `./apps/web/tests/e2e/headers.spec.ts` (+10 -0)
> - Wrote `./apps/web/tests/home.test.tsx` (+12 -0)
> - Wrote `./apps/web/tests/setup.ts` (+1 -0)
> - Wrote `./apps/web/tsconfig.json` (+23 -0)
> - Wrote `./apps/web/vitest.config.ts` (+20 -0)
> - Wrote `./packages/hh-fixtures/.gitkeep` (+1 -0)
> - Wrote `./packages/shared-types/package.json` (+9 -0)
> - Wrote `./packages/shared-types/src/index.ts` (+1 -0)
>
> </details>
>
> A web app mínima também está pronta, com headers e teste Playwright dedicado. Vou ajustar o Makefile para os targets padronizados e então instalar dependências para rodar validações.
>
> <details><summary>Created 1 file</summary>
>
> - Wrote `./Makefile` (+91 -0)
>
> </details>
>
> Makefile normalizado. Vou instalar dependências e deixar os checks apontarem problemas reais; se aparecer incompatibilidade de versão, ajusto o scaffold em vez de empurrar para você.
>
> O Python está instalando, mas o Windows não encontrou `pnpm` no PATH. Vou tentar via Corepack, que é o caminho esperado com Node 20; se também não estiver disponível, deixo isso registrado como bloqueio de ambiente.
>
> A instalação do front está demorando um pouco, mas está avançando pelo Corepack. Observação de ambiente: o Node local é v24, enquanto o projeto fixa Node 20; vou manter a pinagem correta no repo e considerar qualquer falha por engine como ruído local.
>
> Dependências instaladas. Vou rodar agora os checks principais, começando por Python lint/type/test e depois web lint/type/test.
>
> Os checks fizeram o que eu queria: acharam formatação/imports no Python, duas regras B008 do FastAPI, e uma incompatibilidade do ESLint config com Node 24 local. Vou corrigir isso de forma pequena: defaults de Depends como constantes e ESLint flat sem o patch legado do Next.
>
> <details><summary>Edited 2 files</summary>
>
> - Wrote `./apps/api/app/main.py` (+4 -2)
> - Wrote `./apps/web/eslint.config.mjs` (+21 -2)
>
> </details>
>
> O teste web ficou silencioso por mais tempo que o normal depois de iniciar o Vitest. Vou aguardar mais um pouco; se continuar preso, separo o teste em um componente simples ou ajusto a config do Vitest.
>
> Achei dois ajustes claros no Vitest: ele estava coletando os testes Playwright e não conhecia o alias `@`. Vou excluir `tests/e2e` do Vitest e registrar o alias para `src`.
>
> <details><summary>Edited 3 files</summary>
>
> - Wrote `./apps/web/vitest.config.ts` (+7 -0)
> - Wrote `./apps/api/app/core/config.py` (+12 -4)
> - Wrote `./apps/api/app/main.py` (+2 -2)
>
> </details>
>
> Web lint/type/test passou agora, com aviso esperado por Node 24 fora da versão pinada. Vou rerodar o conjunto Python depois do ajuste de tipos.
>
> Os checks Python também estão verdes. Vou validar cobertura/build e a configuração Docker Compose antes de abrir o app local para inspeção visual.
>
> Cobertura ficou por pouco em 79%, então vou adicionar testes unitários pequenos para o branch de produção e o `Base` do SQLAlchemy. Docker não está disponível no PATH deste ambiente, então a validação do compose vai ficar registrada como não executada localmente.
>
> <details><summary>Created 1 file, edited 1 file</summary>
>
> - Wrote `./apps/api/tests/unit/test_db_base.py` (+5 -0)
> - Wrote `./apps/api/tests/unit/test_health.py` (+16 -0)
>
> </details>
>
> O build do Next pegou uma mudança real do Tailwind 4: o plugin PostCSS agora é `@tailwindcss/postcss`. Vou adicionar a dependência e atualizar o PostCSS config.
>
> <details><summary>Edited 2 files</summary>
>
> - Wrote `./apps/web/package.json` (+1 -0)
> - Wrote `./apps/web/postcss.config.mjs` (+1 -1)
>
> </details>
>
> Prettier tentou varrer `.next`, que é artefato de build. Vou excluir artefatos gerados do format check e formatar os arquivos fonte do web.
>
> <details><summary>Created 1 file, edited 1 file</summary>
>
> - Wrote `./apps/web/.prettierignore` (+5 -0)
> - Wrote `./apps/web/eslint.config.mjs` (+1 -0)
>
> </details>
>
> Build, testes e lint do web passaram; o build ainda avisa que não está usando o plugin Next no ESLint por causa da config flat simplificada, mas não bloqueia. Vou subir o dev server e abrir no browser do Codex para uma checagem visual rápida.
>
> <details><summary>Called 3 tools</summary>
>
> MCP tool call
>
> node_repl.js
>
> ```json
> {
>   "title": "Open local web app",
>   "timeout_ms": 30000,
>   "code": "if (!globalThis.agent) {\n  const { setupBrowserRuntime } = await import('C:/Users/manse/.codex/plugins/cache/openai-bundled/browser/26.519.41501/scripts/browser-client.mjs');\n  await setupBrowserRuntime({ globals: globalThis });\n}\nif (!globalThis.browser) {\n  globalThis.browser = await agent.browsers.get('iab');\n}\nawait browser.nameSession('🔎 F0 web check');\nif (typeof tab === 'undefined') {\n  globalThis.tab = await browser.tabs.new();\n}\nawait tab.goto('http://localhost:3000');\nawait tab.playwright.waitForLoadState({ state: 'networkidle', timeoutMs: 10000 });\nconst title = await tab.title();\nconst snapshot = await tab.playwright.domSnapshot();\nnodeRepl.write(JSON.stringify({ title, url: await tab.url(), hasPokerInsight: snapshot.includes('PokerInsight'), hasButton: snapshot.includes('Comecar') }, null, 2));"
> }
> ```
>
> ```text
> Timed out waiting for tab 1 to navigate to http://localhost:3000.
> ```
>
> MCP tool call
>
> node_repl.js
>
> ```json
> {
>   "title": "Verify local web app",
>   "timeout_ms": 30000,
>   "code": "await tab.playwright.waitForLoadState({ state: 'domcontentloaded', timeoutMs: 10000 });\nconst snapshot = await tab.playwright.domSnapshot();\nconst data = {\n  title: await tab.title(),\n  url: await tab.url(),\n  hasPokerInsight: snapshot.includes('PokerInsight'),\n  hasFoundationCopy: snapshot.includes('Skeleton do MVP'),\n  hasButton: snapshot.includes('Comecar')\n};\nnodeRepl.write(JSON.stringify(data, null, 2));"
> }
> ```
>
> ```text
> {
>   "title": "PokerInsight",
>   "url": "http://localhost:3000/",
>   "hasPokerInsight": true,
>   "hasFoundationCopy": true,
>   "hasButton": true
> }
> ```
>
> MCP tool call
>
> node_repl.js
>
> ```json
> {
>   "title": "Capture web screenshot",
>   "timeout_ms": 30000,
>   "code": "const fs = await import('node:fs/promises');\nconst path = 'C:/Users/manse/Desktop/poker-saas-docs/apps/web/f0-homepage.png';\nconst bytes = await tab.screenshot({ fullPage: false });\nawait fs.writeFile(path, Buffer.from(bytes));\nnodeRepl.write(path);"
> }
> ```
>
> ```text
> C:/Users/manse/Desktop/poker-saas-docs/apps/web/f0-homepage.png
> ```
>
> </details>
>
> Browser confirmou a página em `localhost:3000` com título e conteúdo esperados. Vou rodar também o teste Playwright dos headers usando o dev server já ativo.
>
> Estou fazendo uma última passada nos critérios de aceite. Um ponto do TODO pede imagens fixadas por SHA no compose de CI; como Docker não está instalado aqui, vou consultar os digests diretamente no registry para deixar esse arquivo mais próximo do contrato.
>
> <details><summary>Edited 2 files</summary>
>
> - Wrote `./infra/compose.ci.yml` (+3 -3)
> - Wrote `./AGENT_NOTES.md` (+4 -1)
>
> </details>
</details>

F0 Foundation implementada na branch `feat/f0-foundation`.

Principais entregas: monorepo pnpm, hooks Conventional Commits, templates GitHub, compose dev/CI, FastAPI skeleton com health/ready/version, Pydantic Settings, structlog, SQLAlchemy async, Alembic, Next.js skeleton com headers de segurança, testes unitários/E2E e Makefile padronizado.

Validações feitas:
- API: `ruff`, `mypy --strict`, unit tests e coverage `83.53%`
- Web: `lint`, `typecheck`, `format:check`, `vitest`, `next build`
- Playwright headers: `1 passed`
- Browser local: `http://localhost:3000` abriu corretamente

Não consegui validar `docker compose config` porque `docker` não está disponível no PATH deste ambiente. Também não marquei os itens `[x]` no `TODO.md`, porque o protocolo do repo diz para fazer isso após merge do PR.

![Tela inicial](~/AppData/Local/Temp/pokerinsight-f0-homepage.png)

> docker instalado. Revise a fase F0 para ter certeza que não deixou passar nada. Além disso, vi que estava com alguns conflitos em relação à versão do node, estou usando o pnpm para ter versões distintas do node, etão use a versão qe está na documentação ( Apenas deixe uma anotação dos detalhes que perceber para eu revisar depois). Além disso, pq não deu certo de fazer o PR para marcarmos como concluidas as atividades do F0?

<details><summary>25 previous messages</summary>

> Vou fazer uma revisão fechada da F0 contra os critérios do TODO, agora incluindo Docker. Também vou checar como selecionar Node 20 neste ambiente sem mexer globalmente na sua máquina, e deixo as observações em `AGENT_NOTES.md` para revisão.
>
> <details><summary>Ran 4 commands</summary>
>
> - Ran `docker --version; docker compose version`
> - Ran `docker compose -f infra/compose.dev.yml config`
> - Ran `git status --short --branch`
> - Ran `node --version; corepack --version; corepack pnpm --version; Get-Command node | Select-Object -ExpandProperty Source; Get-Command pnpm -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source`
>
> </details>
>
> Docker e Compose agora respondem e o `compose.dev.yml` é válido. A versão ativa de Node ainda é `v24.14.0`, vindo de `C:\nvm4w\nodejs\node.exe`; vou tentar ativar Node 20 via `nvm` nessa sessão e reexecutar os checks do front com a versão correta.
>
> <details><summary>Ran 1 command</summary>
>
> - Ran `nvm version; nvm list`
>
> </details>
>
> Aqui há uma divergência objetiva para suas notas: o ambiente tem `nvm-windows` com Node 24 e 22 instalados, mas não Node 20. Vou instalar/ativar Node 20 via `nvm` para esta validação, mantendo `.nvmrc` e `package.json` como fonte do contrato.
>
> <details><summary>Ran 3 commands</summary>
>
> - Ran `nvm install 20; nvm use 20; node --version; corepack enable; corepack pnpm --version`
> - Ran `Get-Process nvm,node -ErrorAction SilentlyContinue | Select-Object ProcessName,Id,Path`
> - Ran `Stop-Process -Id 9660 -Force`
>
> </details>
>
> O `nvm use 20` instalou o Node 20.20.2, mas falhou ao trocar o symlink com “Acesso negado”. Isso é justamente o tipo de detalhe que vou registrar para você revisar: precisa rodar o terminal como admin ou ajustar permissões do `nvm-windows`. Vou evitar forçar mais e usar o caminho direto do Node 20 instalado para validar o front.
>
> <details><summary>Ran 2 commands</summary>
>
> - Ran `Get-ChildItem C:\Users\manse\AppData\Local\nvm; Get-ChildItem C:\Users\manse\AppData\Local\nvm\v20.20.2 -ErrorAction SilentlyContinue; & C:\Users\manse\AppData\Local\nvm\v20.20.2\node.exe --version; & C:\Users\manse\AppData\Local\nvm\v20.20.2\npm.cmd --version`
> - Ran `& C:\Users\manse\AppData\Local\nvm\v20.20.2\corepack.cmd pnpm --version; & C:\Users\manse\AppData\Local\nvm\v20.20.2\corepack.cmd pnpm --filter @pokerinsight/web lint; & C:\Users\manse\AppData\Local\nvm\v20.20.2\corepack.cmd pnpm --filter @pokerinsight/web typecheck; & C:\Users\manse\AppData\Local\nvm\v20.20.2\corepack.cmd pnpm --filter @pokerinsight/web test`
>
> </details>
>
> A revisão já mostrou alguns pontos que valem correção, não só anotação: o `lint-staged` do web estava formatando mas não lintando, e o Dockerfile do web não combinava com o `context` do compose CI. Vou ajustar isso antes de rodar `compose` de verdade.
>
> <details><summary>Edited 3 files</summary>
>
> - Wrote `./infra/compose.ci.yml` (+14 -1)
> - Wrote `./package.json` (+1 -0)
> - Wrote `./AGENT_NOTES.md` (+4 -0)
>
> </details>
>
> Agora vou validar os dois composes: primeiro sintaxe, depois subir o dev stack para confirmar Postgres/Redis/MinIO, extensões e bucket. Não vou apagar volumes.
>
> <details><summary>Ran 3 commands</summary>
>
> - Ran `docker compose -f infra/compose.dev.yml config`
> - Ran `docker compose -f infra/compose.ci.yml config`
> - Ran `docker compose -f infra/compose.dev.yml up -d`
>
> </details>
>
> O `compose up` está rodando sem erro imediato e provavelmente puxando/subindo imagens em silêncio. Vou aguardar o estado final e em seguida consultar os serviços.
>
> Dev stack subiu. Vou consultar saúde, extensões do Postgres e bucket do MinIO; se algo falhar agora, corrijo o compose.
>
> <details><summary>Ran 4 commands</summary>
>
> - Ran `docker compose -f infra/compose.dev.yml exec -T postgres psql -U pokerinsight -d pokerinsight -c "select extname from pg_extension where extname in ('uuid-ossp','pgcrypto','pg_trgm') order by extname;"`
> - Ran `docker compose -f infra/compose.dev.yml logs --no-color minio-init`
> - Ran `docker compose -f infra/compose.dev.yml ps`
> - Ran `docker compose -f infra/compose.dev.yml exec -T redis redis-cli ping`
>
> </details>
>
> Postgres, Redis e MinIO passaram nos checks, incluindo as três extensões e criação do bucket privado. Vou validar Alembic e o teste de integração com esse stack local, depois faço a passada final de lint/test/build usando Node 20 direto.
>
> <details><summary>Ran 2 commands</summary>
>
> - Ran `$env:APP_ENV='ci'; $env:DATABASE_URL='postgresql+asyncpg://pokerinsight:dev@localhost:5432/pokerinsight'; $env:REDIS_URL='redis://localhost:6379/0'; python -m alembic upgrade head; python -m pytest tests/integration -q`
> - Ran `& C:\Users\manse\AppData\Local\nvm\v20.20.2\corepack.cmd pnpm --filter @pokerinsight/web build; & C:\Users\manse\AppData\Local\nvm\v20.20.2\corepack.cmd pnpm --filter @pokerinsight/web e2e`
>
> </details>
>
> O build com Node 20 passou; o E2E com Node 20 falhou só porque eu invoquei o `corepack` pelo caminho absoluto e o subprocesso do Playwright não herdou `pnpm` no PATH. Vou validar de novo com o PATH do Node 20 na sessão. Também vou eliminar o aviso do plugin Next no ESLint usando o plugin oficial em flat config.
>
> <details><summary>Edited 2 files, ran 4 commands</summary>
>
> - Wrote `./apps/web/eslint.config.mjs` (+6 -0)
> - Ran `$env:Path = 'C:\Users\manse\AppData\Local\nvm\v20.20.2;' + $env:Path
> node --version
> corepack pnpm --filter @pokerinsight/web lint
> corepack pnpm --filter @pokerinsight/web typecheck
> corepack pnpm --filter @pokerinsight/web format:check
> corepack pnpm --filter @pokerinsight/web test
> corepack pnpm --filter @pokerinsight/web build
> corepack pnpm --filter @pokerinsight/web e2e`
> - Wrote `./apps/web/playwright.config.ts` (+1 -1)
> - Ran `$env:Path = 'C:\Users\manse\AppData\Local\nvm\v20.20.2;' + $env:Path
> node --version
> corepack pnpm --filter @pokerinsight/web e2e`
> - Ran `$env:Path = 'C:\Users\manse\AppData\Local\nvm\v20.20.2;' + $env:Path
> corepack pnpm --filter @pokerinsight/web lint
> corepack pnpm --filter @pokerinsight/web typecheck
> corepack pnpm --filter @pokerinsight/web format:check
> corepack pnpm --filter @pokerinsight/web test`
> - Ran `python -m ruff format --check .; python -m ruff check .; python -m mypy --strict app; python -m pytest tests/unit --cov=app --cov-report=term-missing --cov-fail-under=80`
>
> </details>
>
> A suíte principal está verde com Node 20. Agora vou validar pelo menos o build das imagens `api` e `web` do compose CI, porque isso fecha a correção do contexto Docker que encontrei.
>
> <details><summary>Ran 1 command</summary>
>
> - Ran `docker compose -f infra/compose.ci.yml build api web`
>
> </details>
>
> O build Docker da API passou, e o da web encontrou uma falha real: o contexto estava levando artefatos/`node_modules` locais para dentro da imagem e quebrando os links do pnpm. Vou adicionar `.dockerignore` adequado e repetir o build da web.
>
> <details><summary>Created 2 files, ran 1 command</summary>
>
> - Wrote `./.dockerignore` (+18 -0)
> - Wrote `./apps/api/.dockerignore` (+12 -0)
> - Ran `docker compose -f infra/compose.ci.yml build web`
>
> </details>
>
> A imagem web do compose CI agora builda também. Vou parar o stack dev que subi para validação, preservando os volumes, e fechar com um resumo dos achados.
>
> <details><summary>Edited 1 file, ran 5 commands</summary>
>
> - Ran `docker compose -f infra/compose.dev.yml down`
> - Wrote `./AGENT_NOTES.md` (+6 -0)
> - Ran `gh --version`
> - Ran `git remote -v`
> - Ran `git status --short --branch`
> - Ran `gh auth status`
>
> </details>
</details>

Revisei a F0 de ponta a ponta e corrigi alguns pontos que tinham passado:

- `lint-staged` agora roda lint do web também.
- `compose.ci.yml` agora tem `minio-init`, digests SHA nas imagens de infra e build context correto do web.
- Adicionei [.dockerignore](/C:/Users/manse/Desktop/poker-saas-docs/.dockerignore) e [apps/api/.dockerignore](/C:/Users/manse/Desktop/poker-saas-docs/apps/api/.dockerignore), porque o build Docker da web estava levando artefatos locais e quebrando o pnpm.
- Playwright agora usa `corepack pnpm dev`, reduzindo dependência de shim global.
- Registrei os detalhes de Node/nvm em [AGENT_NOTES.md](/C:/Users/manse/Desktop/poker-saas-docs/AGENT_NOTES.md).

Validações feitas agora:
- `docker compose -f infra/compose.dev.yml config`
- `docker compose -f infra/compose.ci.yml config`
- `docker compose -f infra/compose.dev.yml up -d`
- Postgres com `uuid-ossp`, `pgcrypto`, `pg_trgm`
- Redis `PONG`
- MinIO criou bucket `pokerinsight-dev`
- `alembic upgrade head`
- API lint/type/unit coverage/integration verdes
- Web lint/type/format/test/build/e2e verdes com Node `v20.20.2`
- `docker compose -f infra/compose.ci.yml build api web` passou

Sobre Node: instalei `20.20.2` com `nvm install 20`, mas `nvm use 20` falhou com `Acesso negado`. Então validei usando o Node 20 diretamente em `C:\Users\manse\AppData\Local\nvm\v20.20.2`. O PATH ainda aponta para Node 24 via `C:\nvm4w\nodejs\node.exe`.

Sobre o PR: não deu “errado”; eu não criei ainda porque a etapa anterior ficou só como implementação local. Para abrir PR falta fazer commit, push da branch `feat/f0-foundation` e chamar `gh pr create`. Também não marquei o `TODO.md` como concluído porque o próprio protocolo diz marcar `[x]` após merge do PR.

