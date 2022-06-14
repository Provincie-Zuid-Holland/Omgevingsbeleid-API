FROM node:14-bullseye

RUN set -ex; \
    apt update; \
    apt install -y git; \
    rm -rf /var/lib/apt/lists/*rm -rf /var/lib/apt/lists/*;

ENV FRONTEND_BRANCH=${FRONTEND_BRANCH:-dev}
ENV PZH_FONTAWESOME_SECRET=${PZH_FONTAWESOME_SECRET}

RUN set -ex; \
    cd /opt/; \
    git clone https://github.com/Provincie-Zuid-Holland/Omgevingsbeleid-Frontend.git; \
    cd Omgevingsbeleid-Frontend;

WORKDIR /opt/Omgevingsbeleid-Frontend

COPY ./docker/frontend/docker-entrypoint.sh /opt/Omgevingsbeleid-Frontend/docker-entrypoint.sh
RUN  chmod +x /opt/Omgevingsbeleid-Frontend/docker-entrypoint.sh

ENTRYPOINT ["/opt/Omgevingsbeleid-Frontend/docker-entrypoint.sh"]
CMD ["yarn", "start"]
