FROM node:16-bullseye


RUN set -ex; \
    apt update; \
    apt install -y git; \
    rm -rf /var/lib/apt/lists/*rm -rf /var/lib/apt/lists/*;

ARG BUILTIME_FRONTEND_BRANCH=dev
ENV FRONTEND_BRANCH=${BUILTIME_FRONTEND_BRANCH:-dev}

RUN set -ex; \
    cd /opt/; \
    git clone -b ${FRONTEND_BRANCH} https://github.com/Provincie-Zuid-Holland/Omgevingsbeleid-Frontend.git; \
    cd Omgevingsbeleid-Frontend; \
    npm install;

WORKDIR /opt/Omgevingsbeleid-Frontend

CMD ["npm", "start"]
