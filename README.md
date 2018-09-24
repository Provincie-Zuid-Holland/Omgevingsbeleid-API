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

## Deployment
Deployment stappen op een nieuwe VM:

### 1: Python installeren
- Download Python 3.6.x (Windows x86-64 executable installer) op [de website van de Python Software Foundation](https://www.python.org/downloads/windows/).
- Run de installer
    - __!!! Vink `Add Python 3.6 to PATH` & `Install launcher for all users (recommended)` aan op het eerste scherm van de installer!__
- Klik op 'Install Now'
- Test de installatie:
    - Start een nieuwe Command Prompt
    - Typ `python --version`
    - Als er Python 3.6.x verschijnt is Python sucessvol geïnstalleerd.

### 2: Git installeren
- Download de nieuwste versie van Git (64-bit Git for Windows Setup) op [de Git download pagina](https://git-scm.com/download/win)
- Run de installer
    - __Op het scherm `Adjusting your PATH evironment` vink `Use Git from the Windows Command Prompt` aan.__
    - __OP het scherm `Configuring the teminal emulator to use with Git Bash` vink `Use Windows default console window`.__
- Test de installatie:
    - Start een nieuwe Command Prompt
    - Typ `get --version`
    - Als er een git version string verschijnt is Git succesvol geïnstalleerd.

