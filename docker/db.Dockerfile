FROM postgres:17-bookworm
# StagePass DB: PG17 + pgBackRest + rsync (Debian-based, pinned major 17)
RUN apt-get update \
 && apt-get install -y --no-install-recommends pgbackrest rsync \
 && rm -rf /var/lib/apt/lists/* \
 && mkdir -p /var/lib/pgbackrest /var/log/pgbackrest /etc/pgbackrest \
 && chown -R postgres:postgres /var/lib/pgbackrest /var/log/pgbackrest
COPY docker/pgbackrest.conf /etc/pgbackrest/pgbackrest.conf
COPY docker/postgresql-stagepass.conf /etc/postgresql-stagepass.conf
COPY docker/db-entrypoint.sh /usr/local/bin/db-entrypoint.sh
RUN chmod +x /usr/local/bin/db-entrypoint.sh
