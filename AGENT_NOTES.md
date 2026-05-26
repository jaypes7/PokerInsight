# Notas do agente para F0-FOUNDATION

## Decisoes tomadas
- Agrupei a fase F0 em uma unica branch `feat/f0-foundation`, porque o pedido humano foi realizar a fase inteira.
- Usei licenca Proprietary como default, conforme TODO.md.
- Mantive o backend em `apps/api/app` para atender os ACs de F0, com separacao interna `core`, `db` e `observability`.
- Ajustei o Playwright para iniciar o web server via `corepack pnpm dev`, evitando depender do shim `pnpm` global.
- Adicionei `.dockerignore` na raiz e em `apps/api` para impedir que artefatos locais quebrem builds Docker.

## Trade-offs
- Docker nao esta disponivel no PATH deste ambiente; validei sintaxe indiretamente por leitura e fixei digests do compose CI via Docker Registry API.
- O shadcn/ui foi representado por `components.json` e um primitive Button minimo, suficiente para o skeleton.
- `next build` ainda emite aviso dizendo que o plugin Next nao foi detectado no ESLint flat config, mesmo com `@next/eslint-plugin-next` aplicado manualmente. Nao bloqueia lint/build, mas vale revisar quando consolidar a config de ESLint 9 + Next 15.

## Pontos para revisao humana atenta
- Confirmar se a licenca proprietaria deve virar MIT antes de abrir o repositorio.
- Confirmar owners reais em `.github/CODEOWNERS`.
- Confirmar politica de CSP quando integrarem Auth.js, Sentry e analytics.
- Node 20.20.2 foi instalado via `nvm install 20`, mas `nvm use 20` falhou com "Acesso negado"; usar terminal admin ou revisar permissoes do `nvm-windows`.
- O PATH atual ainda aponta para `C:\nvm4w\nodejs\node.exe` com Node 24.14.0; para validar usei o Node 20 diretamente em `C:\Users\manse\AppData\Local\nvm\v20.20.2`.

## Comandos executados que tiveram efeito nao-trivial
- `git switch -c feat/f0-foundation`
- `python -m pip install -r apps/api/requirements-dev.txt`
- `corepack pnpm install`
- `corepack pnpm --filter @pokerinsight/web dev`
- `docker compose -f infra/compose.dev.yml config`
- `nvm install 20`
- `docker compose -f infra/compose.dev.yml up -d`
- `docker compose -f infra/compose.dev.yml down`
- `docker compose -f infra/compose.ci.yml build api web`
