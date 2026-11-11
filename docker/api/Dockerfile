FROM --platform=linux/amd64 python:3.13-trixie

COPY --from=ghcr.io/astral-sh/uv:0.13.1 /uv /uvx /bin/

ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /code

RUN set -ex; \
    apt update; \
    apt upgrade -y; \
    apt install -y build-essential supervisor; \
    mkdir -p /var/log/supervisor; \
    rm -rf /var/lib/apt/lists/*;

COPY --chown=root:root ./docker/api/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=.python-version,target=.python-version \
    uv sync --locked --no-install-project

COPY ./docker/api/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

CMD ["/usr/bin/supervisord"]
