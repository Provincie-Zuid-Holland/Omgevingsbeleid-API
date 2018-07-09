# PZH Flask Graph
Dit is een nieuwe versie van de service laag (API) voor het project 'omgevingsbeleid dashboard' van de provincie Zuid-Holland

## Stack
- Python
    + [Flask](http://flask.pocoo.org/)
    + [Records](https://github.com/kennethreitz/records)
    + [Flask-restful](https://github.com/flask-restful/flask-restful)
    + [Marshmallow](http://marshmallow.readthedocs.io/en/3.0/)
    + [PyODBC] (https://github.com/mkleehammer/pyodbc)
- Bash

## Installeren
Dit project maakt gebruik van [pipenv](https://github.com/pypa/pipenv). Installeer pipenv en voer de volgende commands uit:
```shell
$ pipenv install --dev
```

## Settings.py
Een settings.py file is nodig om de omgevings specifieke instellingen te verkrijgen.
``` python
DB_USER = 'Database gebruiker'
DB_PASS = 'Wacthwoord van gebruiker'
DB_HOST = 'Locatie van SQL-server'
DB_PORT = 'Poort van SQL-server (1433 default)'
DB_NAME = 'Naam van de database'
DB_DRIVER = 'Driver naam'
```

## Lokale versie draaien
Run het script `runflask.sh`
