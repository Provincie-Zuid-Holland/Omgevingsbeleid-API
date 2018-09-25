# PZH Flask Graph
Dit is een nieuwe versie van de service laag (API) voor het project 'omgevingsbeleid dashboard' van de provincie Zuid-Holland

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
- Python moet nu nog worden toegevoegs aan het system PATH
    - klik op `Start` -> `Edit the system environment variables` -> `Environment Variables`
    - Voeg onder `System Variables` de Python locatie toe aan je Path. Je kan de locatie vinden in `User variables for master` 

### 2: Git installeren
- Download de nieuwste versie van Git (64-bit Git for Windows Setup) op [de Git download pagina](https://git-scm.com/download/win)
- Run de installer
    - __Op het scherm `Adjusting your PATH evironment` vink `Use Git from the Windows Command Prompt` aan.__
    - __OP het scherm `Configuring the teminal emulator to use with Git Bash` vink `Use Windows default console window`.__
- Test de installatie:
    - Start een nieuwe Command Prompt
    - Typ `get --version`
    - Als er een git version string verschijnt is Git succesvol geïnstalleerd.

### 3: Gitlab Runner installeren
- Download de nieuwste versie van GitLab Runner (x86) van [de GitLab Runner windows pagina](https://docs.gitlab.com/runner/install/windows.html).
- Maak een map aan `C:\GitLab-Runner` en plaats de gedownloade binary in deze folder.
- Hernoem de binary naar `gitlab-runner.exe`.
- Start een command prompt in administrator mode
- Registreer de runner in de command prompt:
    - `cd C:\GitLab-Runner`
    - `gitlab-runner register`
    - Nu moet je de gitlab runner registreren:
        - `Please enter the gitlab-ci coordinator URL (e.g. https://gitlab.com )` -> `https://gitlab.com`
        - `Please enter the gitlab-ci token for this runner` ->
            - Verkrijg een gitlab token van het project onder `Settings` > `CI/CD` > `Runners (expand)` > `Setup a specific Runner manually`
            - Deze token voer je in als antwoord
        - `Please enter the gitlab-ci description for this runner` -> Naam van de runner (meestal is genoeg 'runner')
        - `Please enter the gitlab-ci tags for this runner (comma separated):` -> Leeglaten
        - `Please enter the executor: ssh, docker+machine, docker-ssh+machine, kubernetes, docker, parallels, virtualbox, docker-ssh, shell:` -> `shell`
    - Stel GitLab runner is als deamon service:
        - `gitlab-runner install`
    - Deze runner zou nu beschikbaar moeten zijn op de Gitlab project pagina (deze pagina) onder `Settings` > `CI/CD` > `Runners (expand)` > `Runners activated for this project`

