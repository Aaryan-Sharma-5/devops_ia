# StagePass + pgBackRest — DevOps IA Case Study

**PostgreSQL Disaster Recovery Using pgBackRest: WAL Archiving, Point-in-Time Recovery and Backup Evaluation**

> Research question: *How does pgBackRest with archived WAL improve PostgreSQL recoverability
> after accidental data loss compared with a consistent file-system snapshot alone, and what are
> the time and storage trade-offs of its backup strategies?*

Fictional event platform **StagePass** (flagship: **KJSCE Garba Eve — 12 October**, plus Maker
Weekend & Open-Air Cinema). A scripted HTTP workload adds 20 Garba registrations, a controlled
`DELETE` wipes the event, and two recovery strategies are compared end-to-end with real row
counts, timings and logs.

**Measured headline:** snapshot-only rsync → 100/120 bookings (20 new lost, ×2 runs);
pgBackRest named PITR → 120/120 with 20/20 new registrations (×2 runs).

## Prerequisites
Docker + Docker Compose, Python 3.11+, ~4 GB free. No cloud, no API keys.
Pinned: PostgreSQL **17.11**, pgBackRest **2.59.3** (see `results/experiment_metadata.json`).

## Quick start
```bash
make up                # build + start (db health-gated before app)
make seed              # deterministic 100 bookings (20/50/30)
make test              # 8 pytest API/seed/safety tests
make demo-rsync        # Scenario A: snapshot-only baseline (~30 s)
make demo-pgbackrest   # Scenario B: PITR (~60 s)
make benchmark         # Exp 2 (+pg_dump): 20k-row modes (~40 s)
make compare           # regenerate charts from CSVs
make report            # charts + DOCX report + PPTX deck
open http://localhost:8000/        # StagePass (12 OCT hero)
open http://localhost:8000/admin   # ops dashboard (live DB counts)
```

## Repository map
- `app/` FastAPI + Jinja2 (`main.py`, `db.py`, `templates/`, `static/`)
- `docker/` DB/app/tools images, `pgbackrest.conf`, PG tuning, init SQL
- `sql/` schema, deterministic seed, controlled incident, verify, reset
- `scripts/` workload, `scenario_rsync.py`, `scenario_pgbackrest.py`, `benchmark.py`,
  `compare.py`, `build_report.py`, `build_pptx.py`, `safety.py`, `common.py`, `seed_helper.py`
- `tests/` API/seed/safety regression tests
- `docs/` plan, API, protocol, **RESULTS**, runbook, sources, report (.docx+.md),
  deck (.pptx), speaker + video scripts
- `results/` raw CSVs/JSON/logs/plots/genuine screenshots

## Key findings (`docs/RESULTS.md`)
| run | recovered | new regs | backup | restore |
|---|---|---|---|---|
| rsync ×2 | 100 | 0/20 lost | ~1 s | ~11–15 s |
| PITR ×2 | 120 | 20/20 | ~7–13 s | ~18–21 s |
| full/diff/incr (20k) | — | — | 10.6/2.5/3.0 s, 4.5 MB/698 KB/636 KB (repo bytes) | — |
| pg_dump -Fc | — | — | 0.3 s, 0.5 MB, no WAL replay | 1.4 s |

## Safety
Destructive scripts require `STAGEPASS_LAB=1`, validate every path, refuse host/unknown
targets, log everything. No destructive app endpoints; no Docker socket in the app.

## Troubleshooting
- `db` unhealthy: `docker compose logs db` (archive-push errors pre-`stanza-create` are normal).
- App 500 on dashboard: fixed GROUP BY regression — rebuild `app` (`docker compose up -d --build app`).
- PITR refuses: required WAL not yet archived — wait, check `pg_stat_archiver`, rerun.
- Port clash: app `:8000`, db `:5433`. Low disk: `docker system prune`, `--rows 5000`.
