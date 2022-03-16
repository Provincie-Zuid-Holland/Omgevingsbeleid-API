<img src="https://omgevingsbeleid.zuid-holland.nl/static/media/PZH_Basislogo.36627253.svg" alt="Provincie Zuid-Holland logo" width="500px">

# Omgevingsbeleid API · ![License](https://img.shields.io/github/license/Provincie-Zuid-Holland/Omgevingsbeleid-API)

[OpenAPI Specification](https://provincie-zuid-holland.github.io/Omgevingsbeleid-API/) 

Omgevingsbeleid API was originally created in early 2018 in order to meet the requirements
given by the new 'Omgevingswet' from the dutch national government.

## Stack
- Python
    + [Flask](http://flask.pocoo.org/)
    + [Flask-restful](https://github.com/flask-restful/flask-restful)
    + [Marshmallow](http://marshmallow.readthedocs.io/en/3.0/)
    + [PyODBC](https://github.com/mkleehammer/pyodbc)
    + [SQLAlchemy](https://github.com/sqlalchemy/sqlalchemy)
- Microsoft SQL Server

## Setup

For development we currently support two setups:
- [Manual installation](#manual-installation)
- [Running in docker](#running-in-docker)

## Manual Installation

## Dependencies

### Ubuntu

Ubuntu users need `unixodbc-dev` to use the PyODBC package"
```
apt install unixodbc-dev
```

## Installation
This project utilizes [venv](https://docs.python.org/3/tutorial/venv.html). Create a new venv.
```shell
python -m venv .venv
```
activate your new venv.
```shell
.venv/Scripts/activate
```
install the required packages.
```shell
pip install -r requirements.txt
```

## Environment Variables
This application requires the following variables to be available
``` bash
DB_USER= Database user that the application can use
DB_PASS= Password of the database user
DB_HOST= SQL-server host URI
DB_PORT= Port to use for connection to SQL-server (1433 default)
DB_NAME= Name of the database to use
DB_DRIVER= Database driver name to use
FLASK_APP= application.py
JWT_SECRET= 1234abahsge (random string)
```
When developing it is convencient to set the FLASK_ENV variable to enable auto reload debugging mode.

```bash
FLASK_ENV=development
```
To run the tests, the application requires a database with a test user in its user table.
Ass the following variables
```bash
TEST_MAIL= Email address of the test user (in user table, optional)
TEST_PASS= Password of the test user (optional)
TEST_UUID= UUID of the test user (optional)
```

## Running locally and running tests
In order to run your local project (requires a valid .env file).
```bash
flask run
```

To run the tests.
```bash
pytest
```

## Running in docker

### Dependencies for docker

- minimum docker version 17.06.0+
- minimum docker-compose version 1.27.0

To initialise the project you can run:
```bash
make init
```

This will start this python project as api, and it will also start the mssql database and frontend application.
Goto [localhost:8888](http://localhost:8888) to view all the services working together.

Note: it can take a while to start as the frontend will be build in development mode.

## Commonly used commands

```bash
make help # Shows the commonly used make commands with a small description
make init # The entrypoint: Starts docker, loads database and fills database with fixtures

make info # Shows information where all the applications can me accessed.
make api  # Sends you in the api container
make logs # Tails the docker-compose logs
make restart # Restarts the docker services and executes `init` afterwards
make restart-hard # Same as restart, but will also remove the current volumes
make test # Run the tests inside the docker container
```

## Use a different frontend branch

By default the `dev` branch of the frontend application will be used.
You can overwrite the branch by setting the environment variable FRONTEND_BRANCH.

For example in the .env file:
```bash
FRONTEND_BRANCH=main
```
