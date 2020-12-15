# Omgevingsbeleid API
Dit project is een API voor omgevingsbeleid van de provincie Zuid-Holland

## Stack
- Python
    + [Flask](http://flask.pocoo.org/)
    + [Flask-restful](https://github.com/flask-restful/flask-restful)
    + [Marshmallow](http://marshmallow.readthedocs.io/en/3.0/)
    + [PyODBC](https://github.com/mkleehammer/pyodbc)
- Microsoft SQL Server

## Installeren
Dit project maakt gebruik van [venv](https://docs.python.org/3/tutorial/venv.html). Maak een venv aan:
```shell
$ python -m venv .venv
```
Activeer de venv:
```shell
$ .venv/Scripts/activate
```
Installeer de benodigde packages:
```shell
$ pip install -r requirements.txt
```

## Omgevingsvariabelen
Deze applicatie verwacht de volgende omgevingsvariabelen
``` bash
DB_USER=Database gebruiker
DB_PASS=Wachtwoord van gebruiker
DB_HOST=Locatie van SQL-server
DB_PORT=Poort van SQL-server (1433 default)
DB_NAME=Naam van de database
DB_DRIVER=Driver naam
FLASK_APP=server.py
JWT_SECRET=1234abahsge
TEST_MAIL= email van test gebruiker (optioneel)
TEST_PASS= wachtwoord van test gebruiker (optioneel)
TEST_UUID= UUID van test gebruiker (optioneel)
```
In development is het makkelijk om ook de FLASK_ENV variabale in te stellen (Niet gebruiken voor productie omgevingen!)

```bash
FLASK_ENV=development
```

## Lokale versie draaien & Tests draaien
Om een lokale omgeving te draaien (vereist geldige .env):
```bash
> flask run
```

Om te testen:
```bash
> pytest
```
