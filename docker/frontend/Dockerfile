FROM node:14-bullseye


RUN set -ex; \
    apt update; \
    apt install -y git; \
    rm -rf /var/lib/apt/lists/*rm -rf /var/lib/apt/lists/*;

RUN set -ex; \
    cd /opt/; \
    git clone -b dev https://github.com/Provincie-Zuid-Holland/Omgevingsbeleid-Frontend.git; \
    cd Omgevingsbeleid-Frontend; \
    npm install;

WORKDIR /opt/Omgevingsbeleid-Frontend

CMD ["npm", "start"]
