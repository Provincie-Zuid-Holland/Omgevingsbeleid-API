FROM python:3.8-buster

WORKDIR /code

RUN set -ex; \
    curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -; \
    curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list; \
    apt update; \
    apt install -y build-essential unixodbc-dev; \
    ACCEPT_EULA=Y apt install -y msodbcsql17; \
    rm -rf /var/lib/apt/lists/*rm -rf /var/lib/apt/lists/*;

COPY requirements.txt /
RUN pip install -r /requirements.txt

COPY ./ .

CMD ["flask", "run"]
