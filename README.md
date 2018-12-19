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
DB_PASS = 'Wachtwoord van gebruiker'
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
    - Start een nieuwe Command Prompt (Niet als administrator!)
    - Typ `python --version`
    - Als er Python 3.6.x verschijnt is Python sucessvol geïnstalleerd.
- Python moet nu nog worden toegevoegd aan het system PATH
    - klik op `Start` -> `Edit the system environment variables` -> `Environment Variables`
    - Voeg onder `System Variables` de Python locatie toe aan je Path. Je kan de locatie vinden in `User variables for master` Let op alleen de verwijzing naar de Python3* map?
    - Voeg ook de map /Scripts/ toe aan je Path, deze bevindt zich in dezelfde folder als je Python locatie.
    - 
### 2: Git installeren
- Download de nieuwste versie van Git (64-bit Git for Windows Setup) op [de Git download pagina](https://git-scm.com/download/win)
- Run de installer
    - Ik zie veel meer opties, zijn die allen "default"?
    - Destination location?
    - Install Components?
    - Start menu folder?
    - Default editor used by Git "Use Vim"?
    - __Op het scherm `Adjusting your PATH evironment` vink `Use Git from the Command Line` aan.__
    - Use https transport backend "Open SSL"?
    - Configure line ending conversions "Checkout Windows Style"
    - __Op het scherm `Configuring the terminal emulator to use with Git Bash` vink `Use Windows default console window`.__
    - Configure extra options "File system caching" and "Git credential Manager" Niet "Symbolic links"

- Test de installatie:
    - Start een nieuwe Command Prompt
    - Typ `git --version`
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
            - Het token onder "Use the following registration token during setup:" voer je in als antwoord
        - `Please enter the gitlab-ci description for this runner` -> Naam van de runner (meestal is genoeg 'runner' maar beter is 'machinenaam-runner')
        - `Please enter the gitlab-ci tags for this runner (comma separated):` -> Leeglaten
        - `Please enter the executor: ssh, docker+machine, docker-ssh+machine, kubernetes, docker, parallels, virtualbox, docker-ssh, shell:` -> `shell`
    - Stel GitLab runner is als deamon service:
        - `gitlab-runner install`
    - Deze runner zou nu beschikbaar moeten zijn op de Gitlab project pagina (deze pagina) onder `Settings` > `CI/CD` > `Runners (expand)` > `Runners activated for this project`
- Op de Gitlab project pagina kun je onder `Settings` > `CI/CD` > `Runners (expand)` > `Runners activated for this project` de runner aanpassen (klik op het edit icoon naast de identifier).
    - Voeg afhankelijk van welke omgeving deze runner draait de volgende tags toe:
        - `acc`, `prod` of `test`
    - Bijvoorbeeld voor een runner op een acc/test server:
        - `acc, test`
- De Gitlab runner kan je instellen via de file `config.toml` in de directory C:\GitLab-Runner
    - onder `[[runners]]` moeten de volgende instellingen staan:
    ```toml
        executor = "shell"
        shell = "powershell"
    ```
    Test de installatie:


### 4: De eerste pipeline draaien
- Ga op de project pagina naar: `CI/CD` > `Pipelines` en klik op `Run Pipeline`
- Kies voor `Create for` een van je relevante omgeving (bijvoorbeeld `test`)
- Klik op `Create Pipeline`
- Je deploy gaat nu draaien, als het afgelopen is zou het volgende resultaat op de server te vinden moeten zijn:
    - Een nieuwe map in `C:\` genaamd `Deployment`
    - In `Deployment` zit voor iedere actieve omgeving (`acc`, `prod`, `test`) een nieuwe map
    - In deze omgevingsmap zit een map genaamd `.venv`
- Herhaal bovenstaande stap tot er voor elke omgeving een map is.
- **Als een van de bovenstaande zaken niet waar zijn, neem dan contact op met de systeembeheerder.**

### 5: Database verbindingen instellen.
- Ga naar de omgevingsmap (i.e. `C:/Deployment/test`)
- Maak een kopie van `example_settings.py` en noem deze `settings.py`
- Open de `settings.py` in een text-editor
- Plaats de juiste waardes:
    - `DB_DRIVER` zal in de meeste gevallen de waarde `SQL Server Native Client 11.0` moeten krijgen

### 6: IIS installeren en instellen
- Installeer IIS d.m.v. de Server Manager
- Accepteer de standaarden tot het scherm `Role Services` verschijnt.
    - Vink `CGI` aan onder `Application Development`
- Voltooi de installatie

- Installeer WFastCGI via PIP:
    - Start een nieuwe Command Prompt as Administrator
    - `pip install wfastcgi` 
    - (You are using pip version 10.0.1, however version 18.1 is available.) ???
    - Als de installatie voltooid is:
    - `wfastcgi-enable`
    - Je krijgt nu een melding dat er een configuratie is toegepast. En ook een pad naar de locatie van het wfastcgi.py script. 
    - Kopieer het `wfastcgi.py` script naar de root van je omgevingsmap(pen). ?????

- Start IIS Manager op
- Maak een nieuwe website aan (n.b. er is maar een website nodig, ook voor meerdere omgevingen!)
- Per omgeving die je wilt aanmaken:
    - Dubbelklik op `Handler Mappings`
    - Klik onder `actions` op `Add Module Mapping`
        - `Request Path` -> `*` wanneer je maar één omgeving wilt maken, anders kan je per omgeving kiezen voor bijvoorbeeld `test/*` zodat deze aplicatie bereikbaar is op `domeinnaam.com/test/`
        - `Module` -> `FastCgiModule`
        - `Executable` -> `[locatie van je python exe]`|`[locatie van je wfastcgi.py in je omgeving]`
        - Bijvoorbeeld: `c:\users\master\appdata\local\programs\python\python36\python.exe|c:\deployment\test\wfastcgi.py`
    - `Name` -> `wfcgi [omgevingsnaam]`
- Klik op `Request Restrictions` en uncheck het `Invoke handler only if request is mapped to:` vinkje
- Klik op ok en bevestig

- Ga in IIS naar de root server en klik op `FastCGI Settings`
- Per handler mapping die je hebt aangemaakt:
    - Klik op `Add Application`
    - `Full path` -> Pad naar `python.exe` in de .venv map in je omgevingsmap (bijv: `c:\Deployment\acc\.venv\scripts\python.exe`)
    - `Arguments` -> Pas naar `wfastcgi.py` in je omgevingsmap (bijv: `c:\Deployment\acc\wfastcgi.py`)
    - Stel de volgende `Environment Variables` in:
        - `PYTHONPATH` -> Pad naar je omgevingsmap (bijv: `c:\Deployment\acc`)
        - `WSGI_HANDLER` -> `server.app` Vaste variabele????
        - `SCRIPT_NAME` -> de foldernaam van je omgevingsmap (bijv: `/test`) soort lokale verwijzing??
        - `WSGI_LOG` -> locatie waarin je wilt loggen, in ons geval de omgevingsmap (bijv: `c:\Deployment\acc\cgi.log`) Bestand (cgi.log) bestaat niet moet deze aangemaakt worden????
    - Reset iis (`iisreset` in de terminal)

### 7: Client credentials genereren
- Run het script `generate_client_creds.sh` in de omgevingsmap Ik zie alleen maar generate_client_creds.ps1 staan execute with powershell (niet openen in Powershell IDE) ????
- Typ de naam van een client - Wat is de naam van de client Mx_Cap?????
- Je krijgt nu nieuwe credentials terug. Kopier de string en deel die met de front-end ontwikkelaars.
- ???? genereert de volgende fout: flask : The term 'flask' is not recognized as the name of a cmdlet, function, script file, or operable program


Als alles gelukt is dan ben je klaar voor deployment!