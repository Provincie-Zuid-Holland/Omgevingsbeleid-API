#!/bin/sh

cd /code

pip install pip pip-tools
pip install -r ./requirements.txt
pip install -r ./requirements-dev.txt

# @todo: add '--proxy-headers' when using nginx
uvicorn main:app --proxy-headers --host 0.0.0.0 --port 80 --reload

# exec "$@"
