FROM postgres:18.3 AS build

ARG AGE_URL=https://github.com/apache/age/releases/download/PG18%2Fv1.8.0-rc0/apache-age-1.8.0-src.tar.gz

RUN apt-get update \
    && apt-get install -y --no-install-recommends --no-install-suggests \
       bison \
       build-essential \
       flex \
       wget \
       ca-certificates \
       postgresql-server-dev-18 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /age
RUN wget -O age.tar.gz "${AGE_URL}" \
    && tar --strip-components=1 -xzf age.tar.gz \
    && rm age.tar.gz

RUN make && make install

FROM postgis/postgis:18-3.6

COPY --from=build /usr/lib/postgresql/18/lib/age.so \
                   /usr/lib/postgresql/18/lib/
COPY --from=build /usr/share/postgresql/18/extension/age--*.sql \
                   /usr/share/postgresql/18/extension/
COPY --from=build /usr/share/postgresql/18/extension/age.control \
                   /usr/share/postgresql/18/extension/

CMD ["postgres", "-c", "shared_preload_libraries=age"]
