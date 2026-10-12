# Sources (accessed 2026-10-12; titles + URLs; claim mapping)

1. pgBackRest User Guide (Debian/Ubuntu, PG17) — https://pgbackrest.org/user-guide.html
   Supports: stanza/repo config, `stanza-create`, `check`, `backup`, `archive-push`
   setup, `restore --type=name --target --target-action=promote` semantics,
   retention/expire, delta restore. Used for all pgBackRest commands/config.
2. pgBackRest Command Reference — https://pgbackrest.org/command.html
   Supports: exact restore/backup/expire/info option definitions cited in report §17.
3. pgBackRest releases (2.59.2 Sep 2026; 2.53.1 added PG17) —
   https://pgbackrest.org/news.html
   Supports: pinned 2.59.3 being current-stable lineage + PG17 support claim.
4. PostgreSQL 17 Backup & Restore — https://www.postgresql.org/docs/current/backup.html
   (physical vs logical, PITR concepts). Supports: report §§9–10, 13.
5. PostgreSQL WAL configuration — https://www.postgresql.org/docs/current/runtime-config-wal.html
   Supports: `archive_mode/command`, `wal_level=replica`, `archive_timeout` settings.
6. `pg_dump` — https://www.postgresql.org/docs/current/app-pgdump.html and
   `pg_restore` — https://www.postgresql.org/docs/current/app-pgrestore.html
   Supports: Experiment 3 method + selective-restore/no-WAL-replay statements.
7. `pg_basebackup` — https://www.postgresql.org/docs/current/app-pgbasebackup.html
   Supports: why file-level base needs WAL for consistency (snapshot-only limit discussion).
