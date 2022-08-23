#!/bin/sh



# @todo: add '--proxy-headers' when using nginx
#uvicorn main:app --proxy-headers --host 0.0.0.0 --port 80 --reload

# Start debugging server. To debug from your host, remote attach your IDE DAP client to
# The socket configured below. Ensure port is exposed from the container
# python -m debugpy --listen 0.0.0.0:5679 main.py

# exec "$@"
