.PHONY: init info up down down-hard restart logs logs-all mysql-wait mssql mssql-cli mssql-create-database-dev mssql-create-database-test mssql-show-databases mssql-show-tables flask-setup-views flask-db-upgrade flask-routes load-fixtures flask test test-verbose
 
init: up mssql-wait mssql-create-database-dev mssql-create-database-test flask-db-upgrade flask-setup-views load-fixtures info


info:
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

up:
	docker-compose up -d

up-build:
	docker-compose up -d --build

down:
	docker-compose down

down-hard:
	docker-compose down -v --remove-orphans

restart: down init

restart-hard: down-hard up-build init

logs:
	docker-compose logs -f --tail=100

logs-all:
	docker-compose logs -f

mssql-wait:
	@while ! docker-compose exec mssql /opt/mssql-tools/bin/sqlcmd -S localhost -U SA -P Passw0rd -Q "select 1;" > /dev/null 2>&1; do sleep 1; done; sleep 2;

mssql:
	docker-compose exec mssql /bin/bash

mssql-cli:
	docker-compose exec mssql /opt/mssql-tools/bin/sqlcmd -S localhost -U SA -P Passw0rd

mssql-create-database-dev:
	@docker-compose exec mssql /opt/mssql-tools/bin/sqlcmd -S localhost -U SA -P Passw0rd -i /opt/sql/init-dev.sql 

mssql-create-database-test:
	@docker-compose exec mssql /opt/mssql-tools/bin/sqlcmd -S localhost -U SA -P Passw0rd -i /opt/sql/init-test.sql 

flask-db-upgrade:
	docker-compose exec api flask db upgrade
	
flask-setup-views:
	docker-compose exec api flask setup-views -y

flask-routes:	
	docker-compose exec api flask routes

api:
	docker-compose exec api /bin/bash

reset-test: mssql-create-database-test test

test:
	docker-compose exec api pytest

test-verbose:
	docker-compose exec api pytest -s

load-fixtures:
	docker-compose exec api flask load-fixtures

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
