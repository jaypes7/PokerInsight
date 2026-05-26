SHELL := /bin/sh

.PHONY: help setup install dev dev-down dev-logs dev-reset test test-unit test-int test-e2e lint format coverage migrate migrate-new seed parse-fixture bench-parser explain clean

help:
	@echo "PokerInsight targets"
	@echo "  make setup              install dependencies"
	@echo "  make dev                start local infra"
	@echo "  make dev-down           stop local infra"
	@echo "  make dev-logs           follow local infra logs"
	@echo "  make dev-reset          reset local infra volumes"
	@echo "  make test               run unit tests"
	@echo "  make test-unit          run fast unit tests"
	@echo "  make test-int           run integration tests"
	@echo "  make test-e2e           run Playwright tests"
	@echo "  make lint               run static checks"
	@echo "  make format             format code"
	@echo "  make coverage           run coverage"
	@echo "  make migrate            run Alembic upgrade"
	@echo "  make migrate-new MSG=x  create Alembic migration"

setup: install

install:
	pnpm install
	cd apps/api && python -m pip install -r requirements-dev.txt

dev:
	docker compose -f infra/compose.dev.yml up -d

dev-down:
	docker compose -f infra/compose.dev.yml down

dev-logs:
	docker compose -f infra/compose.dev.yml logs -f

dev-reset:
	docker compose -f infra/compose.dev.yml down -v
	docker compose -f infra/compose.dev.yml up -d

test:
	cd apps/api && python -m pytest tests/unit -q
	pnpm --filter @pokerinsight/web test

test-unit:
	cd apps/api && python -m pytest tests/unit -q
	pnpm --filter @pokerinsight/web test

test-int:
	cd apps/api && python -m pytest tests/integration -q

test-e2e:
	pnpm --filter @pokerinsight/web e2e

lint:
	cd apps/api && ruff format --check . && ruff check . && mypy --strict app
	pnpm --filter @pokerinsight/web lint
	pnpm --filter @pokerinsight/web typecheck
	pnpm --filter @pokerinsight/web format:check

format:
	cd apps/api && ruff format .
	pnpm --filter @pokerinsight/web format

coverage:
	cd apps/api && python -m pytest tests/unit --cov=app --cov-report=term-missing --cov-fail-under=80
	pnpm --filter @pokerinsight/web test:coverage

migrate:
	cd apps/api && alembic upgrade head

migrate-new:
	@if [ -z "$(MSG)" ]; then echo "Use: make migrate-new MSG='add table'"; exit 1; fi
	cd apps/api && alembic revision --autogenerate -m "$(MSG)"

seed:
	@echo "Seed script will be added with the first database models."

parse-fixture:
	@if [ -z "$(FILE)" ]; then echo "Use: make parse-fixture FILE=packages/hh-fixtures/sample.txt"; exit 1; fi
	@echo "Parser CLI will be added in F1."

bench-parser:
	cd apps/api && python -m pytest tests/benchmarks --benchmark-only

explain:
	@if [ -z "$(QUERY)" ]; then echo "Use: make explain QUERY='SELECT 1'"; exit 1; fi
	@echo "EXPLAIN helper will be wired after DB repositories exist."

clean:
	rm -rf apps/api/.pytest_cache apps/api/.mypy_cache apps/api/.ruff_cache apps/web/.next apps/web/coverage apps/web/playwright-report
