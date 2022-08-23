FROM --platform=linux/amd64 python:3.8-bullseye

WORKDIR /code

RUN set -ex; \
    curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -; \
    curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list; \
    apt update; \
    apt install -y build-essential unixodbc-dev; \
    ACCEPT_EULA=Y apt install -y msodbcsql17 mssql-tools; \
    rm -rf /var/lib/apt/lists/*rm -rf /var/lib/apt/lists/*;

COPY ./docker/api/docker-entrypoint.sh /docker-entrypoint.sh

RUN  chmod +x /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]
