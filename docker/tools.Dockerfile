FROM postgres:17-bookworm
# Backup-tools: same PG major so pgBackRest + pg_dump/pg_restore versions match db.
RUN apt-get update \
 && apt-get install -y --no-install-recommends pgbackrest rsync python3 python3-psycopg2 \
 && rm -rf /var/lib/apt/lists/*
COPY docker/pgbackrest.conf /etc/pgbackrest/pgbackrest.conf
WORKDIR /work
