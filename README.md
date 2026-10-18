# Automated PostgreSQL Backup and Point-in-Time Recovery using pgBackRest

**Automating Database Backups, WAL Archiving, and Disaster Recovery without Cloud Infrastructure**

> **Project Focus:** This project demonstrates how pgBackRest automates PostgreSQL database backups,
> WAL archiving, and disaster recovery. It explores restoring a database to a specific point in time
> after accidental data loss, evaluating recovery time and reliability without requiring cloud infrastructure.

### Project Authors (K. J. Somaiya College of Engineering)
- **Aaryan Sharma** — `16010123012`
- **Anamay Narkar** — `16010123040`
- **Aditya Singh** — `16010123025`
- **Vraj Soni** — `160101220`

**Measured headline:** snapshot-only rsync → 100/120 bookings (**20 new registrations lost**, ×2 runs);
pgBackRest named PITR → 120/120 with **20/20 new registrations recovered** (×2 runs).

## Contents

1. [What this case study is about](#1-what-this-case-study-is-about)
2. [Background concepts](#2-background-concepts-what-each-tool-is)
3. [Why pgBackRest + WAL wins](#3-why-pgbackrest--wal-wins-measured-not-claimed)
4. [Architecture](#4-architecture)
5. [Detailed setup](#5-detailed-setup)
6. [Tour of the app](#6-tour-of-the-app)
7. [API reference](#7-api-reference)
8. [Running the experiments](#8-running-the-experiments)
9. [Results](#9-results)
10. [Repository map](#10-repository-map)
11. [Deliverables (report, PPT, scripts)](#11-deliverables-report-ppt-scripts)
12. [Safety model](#12-safety-model)
13. [Limitations (honest)](#13-limitations-honest)
14. [Troubleshooting](#14-troubleshooting)
15. [References](#15-references)

---

## 1. What this case study is about

**StagePass** is a small fictional event-registration platform. Its flagship event is
**KJSCE Garba Eve — 12 October** (date field `2026-10-12`, shown as a `12 OCT` badge), with two
supporting events — **Maker Weekend** and **Open-Air Cinema** — so the dashboard looks like a
real product. It is a **real app, not a mock-up**: FastAPI + server-rendered pages backed by
PostgreSQL. Registrations submitted in the browser are validated and inserted into real database
rows inside a transaction; the operations dashboard (`/admin`, alias `/ops`) runs live
`COUNT(*)` queries on every page load, so whatever the database contains is exactly what the
evaluator sees.

The story, end to end:

1. The database is seeded with **100 bookings** — 20 Garba Eve, 50 Maker Weekend, 30 Open-Air
   Cinema — with deterministic IDs (`bk_seed_001`…`bk_seed_100`) and synthetic
   `@example.test` attendees.
2. A backup is taken (rsync snapshot in Scenario A, pgBackRest full backup in Scenario B).
3. A script sends **20 legitimate Garba registrations** through the real HTTP API → 120 bookings.
4. A controlled incident — the classic accidental `DELETE` of all Garba Eve bookings — drops the
   Garba count to **0**. The dashboard visibly breaks *because it reads the real database*.
5. We recover, then verify with SQL **and** the browser: did the 20 legitimate registrations survive?

That single question — *how many legitimate transactions survive recovery, and what did it cost
in time and storage?* — is the entire IA. Everything else (backup modes, dump comparison,
charts, report, PPT, demo scripts) exists to answer it with evidence instead of assertions.
The full methodology lives in `docs/EXPERIMENT_PROTOCOL.md`; the numbers live in
`docs/RESULTS.md` and `results/`.

---

## 2. Background concepts (what each tool is)

### 2.1 rsync — file synchroniser: our "snapshot-only" baseline

`rsync` copies files. Here we run `rsync -aHAX --delete <PGDATA>/ /snapshots/rsync-baseline/`
while PostgreSQL is **cleanly stopped** — a running data directory must never be plain-copied
(files change mid-copy and the result is corrupt). The flags mean: `-a` archive mode (recursive,
preserves permissions/timestamps), `-H` hard links, `-A` ACLs, `-X` extended attributes,
`--delete` exact mirror. A manifest (scenario ID, dataset version, timestamp, row counts,
software versions) is written **outside** the copied data. Restoring mirrors the copy back with
the same flags.

This yields a perfectly consistent database **as of snapshot time T** — but by design it replays
nothing after T. The baseline is therefore precisely named *"consistent rsync snapshot **without
an archived-WAL recovery strategy**"*. Fairness note, stated in the report: rsync combined with
a proper WAL strategy could support fuller recovery — we intentionally test snapshot-ONLY,
because "just copy the files" is the naïve strategy many teams implicitly rely on.

### 2.2 PostgreSQL WAL — the write-ahead log

Every change is first recorded in the WAL as a stream of 16 MB segments
(`00000001000000000000000C`, … — first 8 hex digits = timeline, rest = log sequence).
With `archive_mode=on` and `archive_command='pgbackrest --stanza=stagepass archive-push %p'`,
each filled segment is shipped to the backup repository as it completes (`wal_level=replica`,
`archive_timeout=60`). The archived WAL is a complete ordered history of everything the
database did — the raw material for point-in-time recovery. You can watch it work:
`SELECT last_archived_wal FROM pg_stat_archiver;` advances as segments ship.

### 2.3 pgBackRest — backup + WAL manager + restore orchestrator (v2.59.3)

pgBackRest does three jobs in one pinned binary:

- **Physical backups** — copies cluster files into the repo:
  **full** (everything), **differential** (everything changed since the last full),
  **incremental** (everything changed since the last backup of any kind; needs the full chain).
- **WAL archiving/serving** — `archive-push` (called by PostgreSQL per segment) and
  `archive-get` (used during recovery replay).
- **Restore orchestration** — copies a backup back into `PGDATA`, writes the recovery
  configuration, and replays WAL to the requested target before promoting the cluster live.

A **stanza** (`stagepass`, see `docker/pgbackrest.conf`) is pgBackRest's config unit binding one
cluster path (`pg1-path`) to one repository (`repo1-path`). The repo lives on a **separate Docker
volume from the live data**, so a restore can never overwrite its own recovery copy.

Every pgBackRest command we use, and what it does:

| Command | Purpose in this project |
|---|---|
| `stanza-create` | Initialises stanza metadata in the empty repo (required once). Until it runs, `archive-push` fails — those early errors are normal, not a bug. |
| `check` | Verifies config, stanza, paths, permissions and that WAL archiving works (archives a test segment). Proves *health*, not that any particular recovery target exists. |
| `--type=full backup` | Takes the full physical backup the scenarios recover from. |
| `info` / `info --output=json` | Inspects backup labels, timestamps, WAL ranges, and sizes (scripts parse the JSON for evidence). |
| `restore --type=name --target=<point> --target-action=promote` | Rebuilds `PGDATA` from the backup, replays archived WAL exactly to the named restore point, then promotes to a live primary. Refuses to run over existing files — the data directory must be cleaned first (documented procedure) or `--delta` used. |
| `expire --repo1-retention-full=1` | Deletes backups exceeding retention (demonstrated in the isolated lab repo only). |

### 2.4 PITR — point-in-time recovery with a named target

Before the incident we plant a named flag in the WAL with `pg_create_restore_point(name)` and
record its LSN and timestamp. We then **prove** the segment holding it reached the archive
(polling `pg_stat_archiver` *and* the archive directory, with a fail-safe timeout — one real run
aborted here, which is the guard working, see `docs/RESULTS.md`). Only then do we run the
`DELETE` and later restore to that name. PostgreSQL replays history exactly to the flag: all 20
legitimate registrations return, the later `DELETE` is absent. Choosing a target inherently
discards anything after it — a documented property, not a defect.

### 2.5 pg_dump / pg_restore — logical backup (supplementary comparison)

`pg_dump -Fc` exports database *contents* as a portable custom-format archive; `pg_restore`
reloads it (selectively, if wanted). Measured: 0.3 s dump, 0.5 MB artifact, 1.4 s restore of the
same data. Fast and portable — but it cannot replay WAL to a timestamp by itself. Different tool,
different job; measured here so the comparison is honest rather than dismissive.

### 2.6 RTO vs RPO (how we define them)

- **RTO** (how long until usable): measured from the start of the recovery operation to a
  **verified, queryable app** — not merely process exit. Recorded per run in
  `results/experiment_runs.csv` (`restore_duration_seconds`, `application_ready_duration_seconds`).
- **RPO** (how much history is lost): the recovery *target achieved*. In the lab the named target
  sits after all 20 registrations and before the `DELETE`, so zero legitimate transactions are
  lost. Production RPO depends on archive lag and monitoring — we never claim zero RPO in general.

---

## 3. Why pgBackRest + WAL wins (measured, not claimed)

| | Snapshot-only rsync | pgBackRest + WAL (PITR) |
|---|---|---|
| Recovered bookings | **100** (returns to snapshot time) | **120** (replays to chosen target) |
| Legit post-backup regs | **0/20 — lost** | **20/20 — recovered** |
| Backup time | ~1 s (file copy) | ~7–13 s (full physical) |
| Restore → usable app | ~11–15 s | ~18–21 s |
| Routine backup cost | full copy every time | diff 2.5 s / 698 KB, incr 3.0 s / 636 KB vs full 10.6 s / 4.5 MB (repo bytes) |

The recoverability gap (20 transactions) dwarfs the time gap (seconds). WAL archiving is what
moves recovery from *"whatever existed at backup time"* to *"the exact pre-incident target"* —
and differential/incremental backups make the ongoing cost of that safety a fraction of a full.
Note on sizes: pgBackRest reports **compressed repository bytes**; the database's own
`pg_total_relation_size` is reported separately and the two are never conflated. Also, ~5% of
SQL rows changed does *not* mean ~5% of bytes — PostgreSQL writes whole pages and pgBackRest
compresses, which is exactly why we measure instead of assuming.

---

## 4. Architecture

```
browser ──:8000──▶ app (FastAPI + Jinja2, request-scoped DB connections)
                       │  DATABASE_URL …@db:5432/stagepass
                       ▼
                  db (PostgreSQL 17.11 + pgBackRest 2.59.3 + rsync)
                   │  archive-push each WAL segment   │  SQL
                   ▼                                  ▼
   pgbackrest-repo volume ◀── backup-tools ──▶ pgdata volume ──▶ rsync snapshots volume
   (backups + WAL archive,    (guarded rsync +        (live data,        (stopped-cluster
    separate from PGDATA)      restore operator)       wiped before       mirrors + manifest)
                                                   pgBackRest restore)
```

- **`db`** — custom Debian-based `postgres:17` image with matched pgBackRest + rsync binaries.
  WAL archiving is pre-configured (`archive_command` → `archive-push`); config files are in
  version control, secrets are not. Healthcheck gates the app startup so it never queries a
  cold database.
- **`app`** — StagePass UI + documented JSON API. Connections are opened per request with
  retries, so the app rides through the seconds the database is down during a restore instead
  of crashing on a stale pooled connection.
- **`backup-tools`** — same image lineage (identical pgBackRest version), shares the data, repo
  and snapshot volumes. Runs the guarded rsync/pgBackRest operations. `docker compose exec`
  needs a *running* container, so restores (which require PostgreSQL stopped) run here rather
  than in the stopped `db` container; pgBackRest `restore` needs no live DB connection.
- **Volumes** — `pgdata` (live cluster), `pgbackrest-repo` (backups + WAL), `rsync-snapshots`
  (filesystem baselines + manifests), plus the bind-mounted `results/` that survives restarts.

---

## 5. Detailed setup

**Prerequisites:** Linux (tested on Arch), Docker + Docker Compose, Python 3.11+ with
`psycopg2-binary`, `requests`, `pytest` for host-side scripts, ~4 GB free disk. No cloud
accounts, no API keys, no internet needed at runtime. Pinned: PostgreSQL **17.11**
(`17.11-1.pgdg12+2`), pgBackRest **2.59.3** — recorded in `results/experiment_metadata.json`
after every run.

```bash
git clone https://github.com/AnamayNarkar/devops_ia.git
cd devops_ia

# 1. Build + start (db becomes "healthy" before the app starts — enforced by healthchecks)
docker compose up -d --build        # or: make up  (also stanza-creates + seeds; failures non-fatal)
docker compose ps                   # all three containers Up; db (healthy), app (healthy)

# 2. Verify the stack speaks
curl http://localhost:8000/api/health
# {"app":"ok","db":{"status":"ok","version":"PostgreSQL 17.11 ..."}}

# 3. Verify WAL archiving is wired up
docker compose exec -T db su postgres -c \
  "psql -U postgres -d stagepass -tAc 'SHOW archive_mode; SHOW archive_command;'"
# on
# pgbackrest --stanza=stagepass archive-push %p
docker compose exec -T db su postgres -c "pgbackrest --stanza=stagepass check"
# ... check command end: completed successfully

# 4. Seed + test
make seed   # deterministic 100 bookings (20/50/30), rerunnable, never duplicates
make test   # 8 pytest tests: health, events, real-row registration, validation,
            # seed idempotency, dashboard-vs-SQL cross-check, safety path/lab guards
```

Host ports: app `:8000`, PostgreSQL `:5433` (so a local PostgreSQL on 5432 never clashes).
Fresh-machine expectation: build takes a few minutes (three images), first `check` archives its
first WAL segment, `make seed` prints `total bookings: 100`.

---

## 6. Tour of the app

- **`GET /`** — StagePass home: brand bar, Garba/Navratri SVG motif band, `12 OCT` date badge,
  `KJSCE Garba Eve — 12 October` hero with venue/timing/ticket info from seed data, Register Now
  form (name, email, tickets 1–10, backend-validated, returns a booking ID like `bk_9c8f…`),
  live snapshot card, and Maker Weekend / Open-Air Cinema secondary cards. Palette: deep
  maroon/plum, saffron/coral, warm cream. Genuine screenshot: `results/screenshots/home.png`.
- **`GET /admin` (alias `/ops`)** — operations dashboard: Garba bookings KPI (prominent), total
  bookings, attendees, DB health, per-event table, recent registrations with booking IDs. Every
  number is a fresh SQL query — recovery is *visible* here. Genuine screenshot:
  `results/screenshots/admin.png`.
- All attendee data is synthetic (`attendee001@example.test`, …). No emails are sent; no payments.

## 7. API reference

Base URL `http://localhost:8000`. Headline metric everywhere: **booking rows**. Full contracts in
`docs/API.md`; quick examples:

```bash
curl localhost:8000/api/health
curl localhost:8000/api/events                                   # 3 events, Garba dated 2026-10-12
curl localhost:8000/api/dashboard/summary                       # live totals + per-event + recent
curl localhost:8000/api/events/kjsce-garba-eve/registrations
curl localhost:8000/api/registrations/recent?limit=5
curl -X POST localhost:8000/api/events/kjsce-garba-eve/register \
  -H 'Content-Type: application/json' \
  -d '{"name":"Aarav Shah","email":"attendee999@example.test","tickets":2}'
# {"booking_id":"bk_...","event":"kjsce-garba-eve","tickets":2}
```

`POST …/register` validates (name 2–120 chars, email format, tickets 1–10), upserts the attendee
by email, and inserts attendee + booking **in one transaction** (400 on bad input, 404 on unknown
event, 500 rolled back on DB failure). There is deliberately **no destructive endpoint** —
incident SQL runs only via the guarded lab scripts.

---

## 8. Running the experiments

```bash
make demo-rsync       # Scenario A (~30 s): snapshot → 20 HTTP regs → DELETE → restore → 100/20
make demo-pgbackrest  # Scenario B (~60 s): full backup → 20 regs → restore point → DELETE → PITR → 120/40
make benchmark        # Exp 2+3 (~40 s): 20k-row full→diff→incr + pg_dump -Fc comparison
make compare          # regenerate charts from the CSVs (never hand-typed numbers)
make report           # charts + DOCX report + PPTX deck
make logs             # tail db + app logs
make clean            # tear down volumes (wipes lab data + results CSVs)
```

**Scenario A walkthrough** (`scripts/scenario_rsync.py`): reset → assert 100/20 → stop
PostgreSQL → exact-mirror rsync + external manifest → restart → 20 deterministic HTTP
registrations (assert 120/40, all HTTP 200) → incident `DELETE` (Garba → 0; refresh `/admin`
to see it) → stop → guarded mirror-restore → restart → assert 100/20 with 0/20 batch rows.
Recovery to *snapshot time* — NOT PITR.

**Scenario B walkthrough** (`scripts/scenario_pgbackrest.py`): wipe lab repo → reset 100/20 →
`stanza-create` + `check` (output captured) → `--type=full backup` + `info` (label/timing/size
recorded) → same 20-registration workload (new batch) → `pg_create_restore_point(name)` with
LSN/time recorded → `pg_switch_wal()` → **poll until that exact WAL segment is archived**
(abort on timeout or new archiver failures) → same incident → stop → clean `PGDATA` (exact-path
guard) → `restore --type=name … --target-action=promote` via backup-tools → start → confirm the
target in DB logs → assert 120/40, 20/20 batch IDs, 0 orphans → refresh StagePass.

Every invariant is asserted; failures abort with a useful message instead of fictional success.
Each run appends to `results/experiment_runs.csv` under its own `--run-id`
(`rsync-run1/run2`, `pgbackrest-run1/run2` already recorded; rerun with a new ID any time).

---

## 9. Results

Source of truth: `docs/RESULTS.md` + `results/`. Summary of measured runs (host IST = UTC+5:30):

| run | method | baseline → pre → recovered | new regs | backup | restore → app-ready |
|---|---|---|---|---|---|
| rsync-run1 / run2 | snapshot-only, no WAL | 100 → 120 → **100** | **0/20 lost** | ~1 s | ~15 / ~11 s |
| pgbackrest-run1 / run2 | full + named PITR | 100 → 120 → **120** | **20/20** | ~13 / ~7 s | ~18 / ~21 s |

Backup modes (20 000-row bench table, `pg_total_relation_size` ≈ 3.9 MB):
full **10.6 s / 4.5 MB** → differential **2.5 s / 697.7 KB** → incremental **3.0 s / 635.8 KB**
(sizes = pgBackRest-reported compressed repo bytes; DB size 33.5 MB reported separately).
`pg_dump -Fc`: 0.3 s, 507 577 bytes, `pg_restore --clean` 1.4 s, selective restore yes, WAL
replay no. Retention demo: `expire --repo1-retention-full=1` removed only the orphaned full in
the lab repo (`results/logs/pgbackrest-expire-demo.txt`). Charts
(`results/plots/recovery_counts.png`, `backup_durations.png`) are generated from the CSVs by
`scripts/compare.py`.

---

## 10. Repository map

- `app/` — `main.py` (routes/API/pages), `db.py` (request-scoped connections with retry),
  `templates/index.html`, `templates/admin.html`, `static/style.css`, `requirements.txt`
- `docker/` — `db.Dockerfile`, `app.Dockerfile`, `tools.Dockerfile`, `pgbackrest.conf` (stanza
  `stagepass`), `postgresql-stagepass.conf` (archive tuning), `db-entrypoint.sh`,
  `initdb-postgres-role.sql`
- `docker-compose.yml` — app/db/backup-tools + 4 volumes, healthchecks, startup ordering
- `sql/` — `schema.sql` (events/attendees/bookings + indexes), `seed.sql` (100 deterministic
  bookings), `incident.sql` (controlled DELETE), `verify.sql`, `reset.sql`
- `scripts/` — `workload.py`, `scenario_rsync.py`, `scenario_pgbackrest.py`, `benchmark.py`,
  `compare.py`, `build_report.py`, `build_report_pdf.py`, `build_presentation_template.py`,
  `build_presentation_pptxgenjs.js`, `safety.py`, `common.py`, `seed_helper.py`
- `tests/test_api.py` — 8 regression tests (API, validation, seed idempotency, live dashboard
  cross-check, safety guards)
- `docs/` — `IMPLEMENTATION_PLAN.md`, `API.md`, `EXPERIMENT_PROTOCOL.md`, **`RESULTS.md`**,
  `DEMO_RUNBOOK.md`, `SOURCES.md`, `presentation_and_demo_script.md`, `video_recording_script.md`,
  `pgbackrest_case_study_report.docx` (+ `.md` source), `pgbackrest_case_study_report.pdf`,
  `pgbackrest_ia_presentation.pptx`
- `results/` — `experiment_runs.csv`, `backup_benchmarks.csv`, `recovery_benchmarks.csv`,
  `registration_requests.csv` (80/80 HTTP 200), `experiment_metadata.json`, `logs/`, `plots/`,
  `screenshots/`

## 11. Deliverables (report, PPT, scripts)

- **Technical Report (DOCX & Markdown)** `docs/pgbackrest_case_study_report.docx` (+ editable
  `docs/pgbackrest_case_study_report.md` source): all 31 required sections — abstract through
  appendix — with real tables, generated charts, genuine screenshots, inline official-doc
  citations, 100% black font styling, and a references list. Regenerate: `python3 scripts/build_report.py`.
- **Publication-Ready PDF Report** `docs/pgbackrest_case_study_report.pdf`: generated via ReportLab
  with running headers, footers (`Page X of Y`), institutional metadata, and 100% black font.
  Regenerate: `python3 scripts/build_report_pdf.py`.
- **Presentation Deck** `docs/pgbackrest_ia_presentation.pptx`: 16:9, 12 slides built upon the official
  college template (`KJSSE  PPT Template.pptx`), with real screenshots/charts embedded, strict layout
  boundaries (no overflow), and complete speaker notes. Regenerate:
  `python3 scripts/build_presentation_template.py`.
- **Speaker + Demo Script** `docs/presentation_and_demo_script.md`: per-slide wording, terms to
  explain, exact browser/terminal switch moments and expected outputs, 7–10 min run-of-show plus
  fallback plan. **Video script** `docs/video_recording_script.md`: pre-recording checklist, full
  take with timestamps, contingency procedure. **Demo runbook** `docs/DEMO_RUNBOOK.md`: minimal
  reliable live-demo steps.

## 12. Safety model

Every destructive operation: (1) requires `STAGEPASS_LAB=1`; (2) checks the database is the lab
`stagepass` DB; (3) requires the backup/snapshot to exist; (4) validates source/destination
paths and refuses empty, `/`, host PostgreSQL dirs and unexpected targets; (5) prints what it
will change; (6) writes a structured log and exits non-zero on failure. No Docker socket is
exposed to the web app. See `scripts/safety.py` and `docs/EXPERIMENT_PROTOCOL.md`.

## 13. Limitations (honest)

Laptop-local repository (no protection against host-disk failure); lab-scale data and
single-trial bench medians (rerun `--trials 3` on a bigger host); PITR target choice discards
later transactions; success requires the needed backups + WAL to be retained. Deviations found
and fixed during the work (seed-CTE visibility, dashboard GROUP BY + regression test,
restore-via-stopped-container, PGDATA clean step, timeline-aware WAL check, benchmark typo) are
documented in `docs/RESULTS.md` — nothing was silently overwritten.

## 14. Troubleshooting

- `db` unhealthy: `docker compose logs db` — `archive-push` errors *before* the first
  `stanza-create` are expected (nothing to archive into yet).
- Dashboard 500: the GROUP BY regression is fixed in `app/main.py`; rebuild with
  `docker compose up -d --build app`.
- PITR refuses ("required WAL not verified"): archiving is still catching up — check
  `SELECT * FROM pg_stat_archiver;`, wait, rerun.
- `scenario_pgbackrest` fails to connect: a previous run may have left `db` stopped — the
  scripts now `start` it automatically; `docker compose start db` also works.
- Port clash: app `:8000`, db `:5433`. Low disk: `docker system prune`; shrink the bench
  (`python3 scripts/benchmark.py --rows 5000`).
- Reset everything: `make clean` (destroys volumes and result CSVs), then `make up && make seed`.

## 15. References

Authoritative sources first (accessed 2026-10-12; per-claim mapping in `docs/SOURCES.md`):
pgBackRest User Guide <https://pgbackrest.org/user-guide.html> · Command Reference
<https://pgbackrest.org/command.html> · Releases <https://pgbackrest.org/news.html> ·
PostgreSQL Backup & Restore <https://www.postgresql.org/docs/current/backup.html> · WAL
configuration <https://www.postgresql.org/docs/current/runtime-config-wal.html> · pg_dump
<https://www.postgresql.org/docs/current/app-pgdump.html> · pg_restore
<https://www.postgresql.org/docs/current/app-pgrestore.html> · pg_basebackup
<https://www.postgresql.org/docs/current/app-pgbasebackup.html>.
