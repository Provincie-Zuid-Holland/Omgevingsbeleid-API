<img src="https://www.zuid-holland.nl/publish/pages/26873/pzh_basislogo_rgb_1_0.svg" alt="Provincie Zuid-Holland logo" width="220px">

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
- Microsoft SQL Server

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

