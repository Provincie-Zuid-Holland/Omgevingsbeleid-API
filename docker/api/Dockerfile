FROM --platform=linux/amd64 python:3.8-bullseye

WORKDIR /code

RUN set -ex; \
    curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -; \
    curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list; \
    apt-get update; \
    apt-get upgrade -y && \
    apt-get install -y build-essential unixodbc-dev; \
    ACCEPT_EULA=Y apt install -y msodbcsql17 mssql-tools; \
    rm -rf /var/lib/apt/lists/*rm -rf /var/lib/apt/lists/*;

# add supervisor
RUN apt-get update; \
	apt-get install -y supervisor; \
	mkdir -p /var/log/supervisor;
COPY --chown=root:root ./docker/api/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Python packages
COPY requirements.txt /
COPY requirements-dev.txt /
RUN pip install pip-tools; \
	pip install -r /requirements.txt; \
	pip install -r /requirements-dev.txt;

# Startup services
COPY ./docker/api/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

CMD ["/usr/bin/supervisord"]
#ENTRYPOINT ["/docker-entrypoint.sh"]
