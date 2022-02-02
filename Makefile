.PHONY: init info up down down-hard restart logs logs-all mysql-wait mssql mssql-cli mssql-create-database mssql-show-databases mssql-show-tables flask-setup-database flask-setup-tables flask-setup-views flask-routes flask

init: up mssql-create-database info

info:
	@echo ""
	@echo "App:	http://localhost:5000/v0.1/ts_defs"
	@echo ""

up:
	docker-compose up -d --build

down:
	docker-compose down

down-hard:
	docker-compose down -v --remove-orphans

restart: down-hard init

logs:
	docker-compose logs -f --tail=100

logs-all:
	docker-compose logs -f

mysql-wait:
	@while ! docker-compose exec mysql mysqladmin ping -uroot -ppassword --silent; do sleep 1; done; sleep 2;

mssql:
	docker-compose exec mssql /bin/bash

mssql-cli:
	docker-compose exec mssql /opt/mssql-tools/bin/sqlcmd -S localhost -U SA -P Passw0rd

mssql-create-database:
	@docker-compose exec mssql /opt/mssql-tools/bin/sqlcmd -S localhost -U SA -P Passw0rd -i /opt/init.sql 

mssql-show-databases:
	@docker-compose exec mssql /opt/mssql-tools/bin/sqlcmd -S localhost -U SA -P Passw0rd -Q "SELECT name FROM master.dbo.sysdatabases"

mssql-show-tables:
	@docker-compose exec mssql /opt/mssql-tools/bin/sqlcmd -S localhost -U SA -P Passw0rd -Q "SELECT TABLE_NAME FROM db_test.INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'"

flask-setup-database:
	docker-compose exec app flask setup-database

flask-setup-tables:
	docker-compose exec app flask setup-tables

flask-setup-views:
	docker-compose exec app flask setup-views

flask-routes:
	docker-compose exec app flask routes

flask:
	docker-compose exec app /bin/bash
