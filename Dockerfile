# `stage-node` generates some files
FROM node:8-stretch AS stage-node
ADD . /app/src
WORKDIR /app/src
RUN npm install \
    && npm run build:production

# main
FROM python:3.6-alpine3.9
COPY --from=stage-node /app/src/vj4 /app/vj4
COPY --from=stage-node /app/src/LICENSE /app/src/README.md /app/src/requirements.txt /app/src/setup.py /app/
WORKDIR /app

RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.ustc.edu.cn/g' /etc/apk/repositories && \
    apk add --no-cache libmaxminddb \
        libmaxminddb-dev alpine-sdk git && \
    python -m pip install -r requirements.txt && \
    apk del --no-cache --purge \
        libmaxminddb-dev alpine-sdk git && \
    curl "http://geolite.maxmind.com/download/geoip/database/GeoLite2-City.mmdb.gz" | gunzip -c > GeoLite2-City.mmdb

ENV VJ_LISTEN=http://0.0.0.0:8888

ADD docker-entrypoint.py /app/
ENTRYPOINT [ "python", "docker-entrypoint.py" ]

EXPOSE 8888
CMD [ "vj4.server" ]
