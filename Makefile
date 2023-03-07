run:
	uvicorn app.main:app --reload

debug:
	python main.py localhost 8000 8001

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

old-load-database:
	cat scripts/database.sql | sqlite3 api.db

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
