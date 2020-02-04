# PZH Flask Graph
Dit project is een API voor omgevingsbeleid van de provincie Zuid-Holland

## Stack
- Python
    + [Flask](http://flask.pocoo.org/)
    + [Records](https://github.com/kennethreitz/records)
    + [Flask-restful](https://github.com/flask-restful/flask-restful)
    + [Marshmallow](http://marshmallow.readthedocs.io/en/3.0/)
    + [PyODBC](https://github.com/mkleehammer/pyodbc)
- Microsoft SQL Server

## Installeren
Dit project maakt gebruik van [pipenv](https://github.com/pypa/pipenv). Installeer pipenv en voer de volgende commands uit:
```shell
$ pipenv install --dev
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
```

In development is het makkelijk om ook de FLASK_ENV variabale in te stellen (Niet gebruiken voor productie omgevingen!)

```bash
FLASK_ENV=development
```


## Lokale versie draaien
```bash
> flask run
```