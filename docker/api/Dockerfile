FROM --platform=linux/amd64 python:3.13-trixie

WORKDIR /code

RUN set -ex; \
    apt update; \
    apt upgrade -y; \
    apt install -y build-essential odbc-postgresql unixodbc unixodbc-dev supervisor; \
    mkdir -p /var/log/supervisor; \
    rm -rf /var/lib/apt/lists/*rm -rf /var/lib/apt/lists/*; \
    echo "/usr/lib/x86_64-linux-gnu/odbc" > /etc/ld.so.conf.d/odbc.conf; \
    ldconfig;

COPY --chown=root:root ./docker/api/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

COPY requirements.txt /
COPY requirements-dev.txt /
RUN pip install pip-tools; \
	pip install -r /requirements.txt; \
	pip install -r /requirements-dev.txt;

COPY ./docker/api/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

CMD ["/usr/bin/supervisord"]
