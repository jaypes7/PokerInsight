FROM node:20-bookworm-slim AS deps
WORKDIR /app
RUN corepack enable
COPY package.json pnpm-lock.yaml* pnpm-workspace.yaml ./
COPY apps/web/package.json apps/web/package.json
RUN pnpm install --filter @pokerinsight/web --frozen-lockfile

FROM deps AS build
COPY apps/web apps/web
RUN pnpm --filter @pokerinsight/web build

FROM node:20-bookworm-slim AS runtime
WORKDIR /app
ENV NODE_ENV=production
RUN corepack enable && useradd --create-home --shell /usr/sbin/nologin appuser
COPY --from=build /app/apps/web/.next apps/web/.next
COPY --from=build /app/apps/web/public apps/web/public
COPY --from=build /app/apps/web/package.json apps/web/package.json
COPY --from=deps /app/node_modules node_modules
USER appuser
EXPOSE 3000
CMD ["pnpm", "--dir", "apps/web", "start"]
