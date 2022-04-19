#!/bin/sh

COLOR_GREEN='\033[0;32m'
COLOR_NC='\033[0m'

cd /opt/Omgevingsbeleid-Frontend/
git fetch

printf "\n\nUsing frontend branch: ${COLOR_GREEN}${FRONTEND_BRANCH}${COLOR_NC}\n\n\n"

git checkout ${FRONTEND_BRANCH}
git pull
yarn install

exec "$@"
