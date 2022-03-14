.PHONY: init info up down down-hard restart logs logs-all mysql-wait mssql mssql-cli mssql-create-database-dev mssql-create-database-test mssql-show-databases mssql-show-tables flask-setup-views flask-db-upgrade flask-routes load-fixtures flask test test-verbose check-requirements

.DEFAULT_GOAL := help
default: help;
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'


init: up mssql-create-database-dev mssql-create-database-test flask-db-upgrade flask-setup-views load-fixtures info ## --> Starts docker services and loads the database <--

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
	@echo "		Backend:	http://localhost:5000/v0.1/ts_defs"
	@echo "		Mssql:		localhost:11433"
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

flask-db-upgrade: ## Run database migrations
	docker-compose exec api flask db upgrade

flask-setup-views: ## Run database views
	docker-compose exec api flask setup-views -y

flask-routes: ## Show flask routes
	docker-compose exec api flask routes

test: up mssql-create-database-test ## Run the tests
	docker-compose exec api pytest

test-verbose: up mssql-create-database-test	## Run the tests in verbose mode
	docker-compose exec api pytest -s

load-fixtures: ## This will load the fixtures (happends as part of `init`)
	docker-compose exec api flask load-fixtures

# Specific setup without automatically waiting for sql server
setup-no-wait: mssql-create-database-dev mssql-create-database-test flask-db-upgrade flask-setup-views load-fixtures info

# Very rare utilities
mssql-clear-database:
	@docker-compose exec mssql /opt/mssql-tools/bin/sqlcmd -S localhost -U SA -P Passw0rd -i /opt/sql/clear.sql

mssql-show-databases:
	@docker-compose exec mssql /opt/mssql-tools/bin/sqlcmd -S localhost -U SA -P Passw0rd -Q "SELECT name FROM master.dbo.sysdatabases"

mssql-show-tables:
	@docker-compose exec mssql /opt/mssql-tools/bin/sqlcmd -S localhost -U SA -P Passw0rd -Q "SELECT TABLE_NAME FROM db_dev.INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'"

# @deprecated
mssql-load-old-database:
	@docker-compose exec mssql /opt/mssql-tools/bin/sqlcmd -S localhost -U SA -P Passw0rd -i /opt/sql/old.hidden.sql

# deprecated
mssql-load-old-full-database:
	@docker-compose exec mssql /opt/mssql-tools/bin/sqlcmd -S localhost -U SA -P Passw0rd -i /opt/sql/old-full.hidden.sql

# @TODO: DB_DRIVER should be filled in
# This value is different for linux and windows users
# It could be passed in by the .env file
# But i dont like installing that driver locally mmmm
#
# Other options are
# * Run inside container and manually change permissions of created file
# * Run inside container as host user (not sure if that works on Windows)
ifeq (flask-shell, $(firstword $(MAKECMDGOALS)))
  RUN_ARGS := $(wordlist 2, $(words $(MAKECMDGOALS)), $(MAKECMDGOALS))
  $(eval $(RUN_ARGS):;@:)
endif
flask-shell:
	FLASK_APP=application.py DB_USER=SA DB_PASS=Passw0rd DB_HOST=localhost DB_PORT=11433 DB_NAME=db_dev flask $(RUN_ARGS)
