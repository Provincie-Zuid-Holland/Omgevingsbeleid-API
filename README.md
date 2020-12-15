![Provincie Zuid-Holland logo](https://www.zuid-holland.nl/publish/pages/3/provincie_zuid-holland.png)
# Omgevingsbeleid API
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
DB_USER=Database user
DB_PASS=password of user
DB_HOST=Location of SQL-server
DB_PORT=Port of SQL-server (1433 default)
DB_NAME=Name of the database
DB_DRIVER=Driver name
FLASK_APP=server.py
JWT_SECRET=1234abahsge
TEST_MAIL= email of test user (optional)
TEST_PASS= password of test user (optional)
TEST_UUID= UUID of test user (optional)
```
When developing it is convencient to set the FLASK_ENV variable to enable auto reload debugging mode.

```bash
FLASK_ENV=development
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
