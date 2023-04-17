.DEFAULT_GOAL := help
default: help;
.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'


# Commands justs for local env development
run:
	uvicorn app.main:app --reload

debug:
	python app/main.py localhost 8000 8001

local-env:
	pip install -U pip pip-tools==6.8.0
	pip-sync requirements.txt requirements-dev.txt

local-pip-compile:
	pip install -U pip pip-tools==6.8.0
	pip-compile requirements.in
	pip-compile requirements-dev.in

local-pip-upgrade:
	pip install -U pip pip-tools==6.8.0
	pip-compile --upgrade requirements.in
	pip-compile --upgrade requirements-dev.in

drop-database:
	python cmds.py drop-db

init-database:
	python cmds.py init-db

load-fixtures:
	python cmds.py load-fixtures

reset-test-database: drop-database init-database load-fixtures

fix:
	python -m black app/
	python -m autoflake -ri --exclude=__init__.py --remove-all-unused-imports app/

check-security:
	python -m bandit --configfile bandit.yml -r app/

testx:
	python -m pytest -vv -x


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
	@docker compose exec mssql /opt/mssql-tools/bin/sqlcmd -S localhost -U SA -P Passw0rd -i /opt/sql/init-dev.sql

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

# load-fixtures:
# 	python cmds.py load-fixtures


# docker-reset-test-database:

