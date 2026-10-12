#!/bin/bash
set -e
# Ensure pgBackRest dirs exist with right ownership, inject our WAL config include,
# then hand off to the stock postgres entrypoint.
mkdir -p /var/lib/pgbackrest /var/log/pgbackrest
chown -R postgres:postgres /var/lib/pgbackrest /var/log/pgbackrest 2>/dev/null || true
exec docker-entrypoint.sh "$@"
