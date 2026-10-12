# How does pgBackRest with archived WAL improve PostgreSQL recoverability after accidental data loss compared with a consistent file-system snapshot alone, and what are the time and storage trade-offs of its backup strategies?

Generated 2026-10-13 from results/*.csv. Full text in the DOCX; this source mirrors its structure and tables.

## Runs
| run | baseline | pre | recovered | new | backup_s | restore_s |
|---|---|---|---|---|---|---|
| rsync-run1 | 100 | 120 | 100 | 0 | 1.1 | 15.0 |
| pgbackrest-run1 | 100 | 120 | 120 | 20 | 13.3 | 17.6 |
| rsync-run2 | 100 | 120 | 100 | 0 | 0.5 | 10.6 |
| pgbackrest-run2 | 100 | 120 | 120 | 20 | 7.2 | 20.6 |