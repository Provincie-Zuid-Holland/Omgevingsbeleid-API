
.DEFAULT_GOAL := help
default: help;
.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: init
init: up mssql-create-database-dev mssql-create-database-test db-upgrade load-fixtures info ## --> Starts docker services and loads the database <--

.PHONY: info
info: ## Display information how to access services
	@echo ""
	@echo ""
	@echo "	You can access the api inside docker via:"
	@echo "		make api"
	@echo ""
	@echo "	Both services under a proxy: (you probably want this)"
	@echo "		Web:		http://localhost:8888"
	@echo ""
	@echo "	Direct locations:"
	@echo "		Frontend:	http://localhost:3000"
	@echo "		Backend:	http://localhost:8000/docs/"
	@echo "		Mssql:		localhost:11433"
	@echo "     					user=SU password=Passw0rd"
	@echo "		Geoserver:	http://localhost:8080/geoserver"
	@echo "     					user=admin password=password"
	@echo "     					Note: Geoserver takes a while to start"
	@echo ""
	@echo ""

up: ## Starts the docker services
	docker-compose up -d --build

down: ## Stops the docker services
	docker-compose down

down-hard: ## Stops the docker services, will also remove volumes and orphans
	docker-compose down -v --remove-orphans

restart: down init ## Alias for `down` and `init`

restart-hard: down-hard init ## Alias for `down-ard` and `init`

logs: ## Shows and tails the recent docker-compose logs
	docker-compose logs -f --tail=100

logs-all: ## Shows and tails all docker-compose logs
	docker-compose logs -f

api: ## Exec into the api
	docker-compose exec api /bin/bash

mssql: ## Exec into mssql
	docker-compose exec mssql /bin/bash

mssql-cli: ## Sqlcmd in mssql
	docker-compose exec mssql /opt/mssql-tools/bin/sqlcmd -S localhost -U SA -P Passw0rd

mssql-create-database-dev:
	@docker-compose exec mssql /opt/mssql-tools/bin/sqlcmd -S localhost -U SA -P Passw0rd -i /opt/sql/init-dev.sql

mssql-create-database-test:
	@docker-compose exec mssql /opt/mssql-tools/bin/sqlcmd -S localhost -U SA -P Passw0rd -i /opt/sql/init-test.sql

db-upgrade: ## Run database migrations
	docker-compose exec api python -m alembic upgrade head

flask-routes: ## Show flask routes
	docker-compose exec api flask routes

test: up mssql-create-database-test ## Run the tests	
	docker-compose exec api pytest

test-verbose: up mssql-create-database-test	## Run the tests in verbose mode
	docker-compose exec api pytest -s

load-fixtures: ## This will load the fixtures (happens as part of `init`)
	docker-compose exec api python cmds.py initdb


pip-compile:
	docker-compose exec api python -m piptools compile requirements.in

fix:
	docker-compose exec api python -m black app/
	docker-compose exec api python -m autoflake -ri --exclude=__init__.py --remove-all-unused-imports app/
