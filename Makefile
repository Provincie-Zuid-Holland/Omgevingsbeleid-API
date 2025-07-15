.DEFAULT_GOAL := help
default: help;
.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'


.PHONY: prepare-env
VENV   := .venv
PYTHON := $(shell pyenv which python)

prepare-env:
	@echo "→ Creating virtualenv at $(VENV)/…"
	@$(PYTHON) -m venv $(VENV)
	@echo "→ Activating $(VENV) and upgrading pip…"
	@. $(VENV)/bin/activate && pip install --upgrade pip
	@echo "→ Installing runtime dependencies…"
	@. $(VENV)/bin/activate && pip install -r requirements.txt
	@echo "→ Installing development dependencies…"
	@. $(VENV)/bin/activate && pip install -r requirements-dev.txt
	@echo "✅ Environment ready! Activate with: source $(VENV)/bin/activate"


# Commands justs for local env development
run:
	uvicorn app.main:app --reload

debug:
	python app/main.py localhost 8000 8001

pip-sync:
	pip install -U pip pip-tools
	pip-sync requirements.txt requirements-dev.txt

pip-compile:
	pip install -U pip pip-tools
	pip-compile requirements.in
	pip-compile requirements-dev.in

pip-upgrade:
	pip install -U pip pip-tools
	pip-compile --upgrade requirements.in
	pip-compile --upgrade requirements-dev.in

drop-database:
	python -m app.cmds dropdb

init-database:
	python -m app.cmds initdb

load-fixtures:
	python -m app.cmds load-fixtures

reset-test-database: drop-database init-database load-fixtures

check:
	python -m ruff check ./app/

format:
	python -m ruff format ./app/


fix:
	python -m isort app/
	python -m black app/ stubs/
	python -m autoflake -ri --exclude=__init__.py --remove-all-unused-imports app/ stubs/

test:
	python -m pytest

testx:
	python -m pytest -vv -x

testcase:
	python -m pytest -s -vvv -x -k ${case}

# Ment to test MSSQL
docker-init: docker-up docker-mssql-create-database-dev docker-alembic-do-upgrade

docker-up: ## Starts the docker services
	docker compose up -d --build --wait

docker-down: ## Stops the docker services, will also remove volumes and orphans
	docker compose down -v --remove-orphans

docker-restart: docker-down docker-init

docker-api: ## Exec into api
	docker compose exec api /bin/bash

docker-mssql: ## Exec into mssql
	docker compose exec mssql /bin/bash

docker-mssql-create-database-dev:
	@docker compose exec mssql /opt/mssql-tools18/bin/sqlcmd -S localhost -U SA -P Passw0rd -C -i /opt/sql/init-dev.sql

docker-drop-database:
	docker compose exec api python cmds.py drop-db

docker-init-database:
	docker compose exec api python cmds.py init-db

docker-alembic-create-revision:
	docker compose exec api python -m alembic revision --autogenerate

docker-alembic-show-upgrade:
	docker compose exec api python -m alembic upgrade head --sql

docker-alembic-do-upgrade:
	docker compose exec api python -m alembic upgrade head

docker-mssql-setup-search:
	docker compose exec api python cmds.py mssql-setup-search-database

docker-load-fixtures:
	docker compose exec api python cmds.py load-fixtures

# @todo: these docker-test are not finished yet
docker-test:
	docker compose exec api python -m pytest

docker-testx:
	docker compose exec mssql /opt/mssql-tools18/bin/sqlcmd -S localhost -U SA -P Passw0rd -C -i /opt/sql/init-test.sql
	docker compose exec api python -m pytest -vv -x

