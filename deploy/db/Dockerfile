# the official postgis image is amd64 only, this builds on arm64 too (oracle ampere)
FROM postgres:17-bookworm
RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql-17-postgis-3 \
    && rm -rf /var/lib/apt/lists/*
# runs once, when the database is first created
COPY init.sql /docker-entrypoint-initdb.d/
