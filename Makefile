.DEFAULT_GOAL := help

RUN := uv run

.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'


# ---------------------------------------------------------------------------
# Local development
# ---------------------------------------------------------------------------

.PHONY: run debug
run: ## Run the API with auto-reload
	$(RUN) uvicorn app.main:app --reload

debug: ## Run the API in debug mode
	$(RUN) python app/main.py localhost 8000 8001


# ---------------------------------------------------------------------------
# Local database
# ---------------------------------------------------------------------------

.PHONY: drop-database init-database load-fixtures reset-test-database
drop-database: ## Drop the local database
	$(RUN) python -m app.cmds dropdb

init-database: ## Create the local database
	$(RUN) python -m app.cmds initdb

load-fixtures: ## Load fixtures into the local database
	$(RUN) python -m app.cmds load-fixtures

reset-test-database: drop-database init-database load-fixtures ## Drop, create and fill the local database


# ---------------------------------------------------------------------------
# Lint & format
# ---------------------------------------------------------------------------

.PHONY: check check-fix format fix
check: ## Check lint and formatting without fixing (also used in CI)
	$(RUN) ruff check ./app/ ./tests/
	$(RUN) ruff format --check ./app/ ./tests/

check-fix: ## Fix lint issues found by Ruff
	$(RUN) ruff check --fix ./app/ ./tests/

format: ## Format code with Ruff
	$(RUN) ruff format ./app/ ./tests/

fix: check-fix format ## Fix lint issues and format the code


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

.PHONY: test testx testcase testcov
test: ## Run all tests
	$(RUN) python -m pytest

testx: ## Run tests verbose, stop at first failure
	$(RUN) python -m pytest -vv -x

testcase: ## Run tests matching a name: make testcase case=<name>
	$(RUN) python -m pytest -s -vvv -x -k $(case)

testcov: ## Run tests with coverage (XML report)
	$(RUN) python -m pytest --cov --cov-report=xml


# ---------------------------------------------------------------------------
# Docker
# ---------------------------------------------------------------------------

.PHONY: docker-init docker-up docker-down docker-restart docker-api \
	docker-drop-database docker-init-database docker-load-fixtures \
	docker-alembic-create-revision docker-alembic-show-upgrade docker-alembic-do-upgrade \
	docker-psql
docker-init: docker-up docker-alembic-do-upgrade ## Start services and run migrations

docker-up: ## Start the docker services
	docker compose up -d --build --wait

docker-down: ## Stop the docker services, also removes volumes and orphans
	docker compose down -v --remove-orphans

docker-restart: docker-down docker-init ## Recreate everything from scratch

docker-api: ## Open a shell in the api container
	docker compose exec api /bin/bash

docker-drop-database: ## Drop the database in docker
	docker compose exec api python -m app.cmds dropdb

docker-init-database: ## Create the database in docker
	docker compose exec api python -m app.cmds initdb

docker-load-fixtures: ## Load fixtures into the docker database
	docker compose exec api python -m app.cmds load-fixtures

docker-alembic-create-revision: ## Autogenerate a new Alembic migration
	docker compose exec api python -m alembic revision --autogenerate

docker-alembic-show-upgrade: ## Show the SQL for pending migrations
	docker compose exec api python -m alembic upgrade head --sql

docker-alembic-do-upgrade: ## Apply pending migrations
	docker compose exec api python -m alembic upgrade head

docker-psql: ## Open psql in the postgres container
	docker compose exec -it postgres psql -U omgevingsbeleid omgevingsbeleid
