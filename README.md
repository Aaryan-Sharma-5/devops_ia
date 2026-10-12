# StagePass + pgBackRest — DevOps IA Case Study

**PostgreSQL Disaster Recovery Using pgBackRest: WAL Archiving, Point-in-Time Recovery and Backup Evaluation**

> Research question: *How does pgBackRest with archived WAL improve PostgreSQL recoverability
> after accidental data loss compared with a consistent file-system snapshot alone, and what are
> the time and storage trade-offs of its backup strategies?*

**Measured headline:** snapshot-only rsync → 100/120 bookings (**20 new registrations lost**, ×2 runs);
pgBackRest named PITR → 120/120 with **20/20 new registrations recovered** (×2 runs).

---

## 1. What this case study is about

**StagePass** is a small fictional event-registration platform. Its flagship event is
**KJSCE Garba Eve — 12 October** (plus two filler events, Maker Weekend and Open-Air Cinema,
so the dashboard looks realistic). It is a real app — FastAPI + PostgreSQL — not a mock-up:
registrations submitted in the browser land in real database rows, and the operations
dashboard (`/admin`) renders live `COUNT(*)` queries on every load.

The story we demonstrate:

1. The database is seeded with **100 bookings** (20 Garba / 50 Maker / 30 Cinema).
2. A backup is taken (rsync snapshot in Scenario A, pgBackRest full backup in Scenario B).
3. A script sends **20 legitimate registrations** through the HTTP API → 120 bookings.
4. A controlled incident — an accidental `DELETE` of all Garba Eve bookings — drops Garba to **0**.
   The dashboard visibly breaks because it reads the real database.
5. We recover, and check: did the 20 legitimate registrations survive?

That single question — *how many legitimate transactions survive recovery, and what did it
cost in time and storage?* — is the whole IA. Everything else (modes, dumps, charts, report,
PPT) exists to answer it with evidence instead of assertions.

---

## 2. Background concepts (what each tool is)

### rsync — file synchroniser, our "snapshot-only" baseline
`rsync -aHAX --delete` copies the PostgreSQL data directory bit-for-bit to a separate location
while PostgreSQL is **cleanly stopped** (a running data directory must never be plain-copied).
Restoring mirrors the copy back. This gives a perfectly consistent database **as of snapshot
time T** — but by design it replays nothing that happened after T. In this project the baseline
is deliberately named *"consistent rsync snapshot **without an archived-WAL recovery strategy**"*:
rsync combined with WAL archiving could do more, but we test snapshot-ONLY, because that is the
naïve "just copy the files" strategy many teams implicitly rely on.

### PostgreSQL WAL — the write-ahead log
Every change is first recorded in the WAL (write-ahead log) as a stream of segments. With
`archive_mode=on` and `archive_command = pgbackrest … archive-push %p`, each filled segment is
shipped to a backup repository as it completes. The archived WAL is a complete, ordered history
of everything the database did — the raw material for point-in-time recovery.

### pgBackRest — backup + WAL manager + restore orchestrator
pgBackRest (here **v2.59.3**) does three jobs: (a) takes physical backups
(**full** = everything, **differential** = since last full, **incremental** = since last backup
of any kind); (b) archives and serves WAL segments (`archive-push` / `archive-get`); (c) restores
a backup and replays WAL up to a chosen target, then promotes the cluster to live use. A
**stanza** (`stagepass`) is just its config unit binding one cluster to one repository, which is
kept on a **separate volume from the live data** so a restore can never eat its own recovery copy.

### PITR — point-in-time recovery with a named target
Before the incident we plant a named flag in the WAL (`pg_create_restore_point(...)`), verify
that segment is actually archived (our script **refuses** to proceed otherwise — one run really
did abort on this guard), then restore with `--type=name --target=<flag> --target-action=promote`.
PostgreSQL replays history exactly to that flag: every legitimate registration is back, the
later `DELETE` is absent.

### pg_dump — logical backup (supplementary comparison)
`pg_dump -Fc` exports the database contents as a portable archive; `pg_restore` reloads it.
Fast and selective, but it cannot replay WAL to a timestamp by itself — a different tool for a
different job, measured here so the comparison is honest.

## 3. Why pgBackRest + WAL is better (measured, not claimed)

| | Snapshot-only rsync | pgBackRest + WAL (PITR) |
|---|---|---|
| Recovered bookings | **100** (returns to snapshot time) | **120** (replays to chosen target) |
| Legit post-backup regs | **0/20 — lost** | **20/20 — recovered** |
| Backup time | ~1 s (file copy) | ~7–13 s (full physical) |
| Restore → usable app | ~11–15 s | ~18–21 s |
| Routine backup cost | full copy every time | diff 2.5 s/698 KB, incr 3.0 s/636 KB vs full 10.6 s/4.5 MB |

The recoverability gap (20 transactions) dwarfs the time gap (seconds). WAL archiving is what
moves recovery from *"whatever existed at backup time"* to *"the exact pre-incident target"*.
Full evidence: `docs/RESULTS.md`, `results/experiment_runs.csv`, `results/plots/`.

---

## 4. Detailed setup

**Prerequisites:** Linux (tested on Arch), Docker + Docker Compose, Python 3.11+ with
`psycopg2`/`requests`/`pytest` for the host-side scripts, ~4 GB free disk. No cloud accounts,
no API keys, no internet needed at runtime. Pinned versions: PostgreSQL **17.11**,
pgBackRest **2.59.3** (recorded in `results/experiment_metadata.json`).

```bash
git clone https://github.com/AnamayNarkar/devops_ia.git
cd devops_ia
docker compose up -d --build   # or: make up
# wait ~30 s: db must be "healthy" before app starts (healthchecks enforce this)
docker compose ps
curl http://localhost:8000/api/health   # {"app":"ok","db":{"status":"ok",...}}
```

What `make up` builds: `db` (custom Debian PG17 image + pgBackRest + rsync, WAL archiving
pre-configured, repo on its own volume), `app` (StagePass on `:8000`), `backup-tools`
(rsync/pgBackRest operator sharing the data + repo + snapshot volumes). Host ports: app
`:8000`, PostgreSQL `:5433`.

```bash
make seed   # deterministic 100 bookings (20/50/30); rerunnable, no duplicates
make test   # 8 pytest tests: API, validation, seed idempotency, safety guards
```

Open **http://localhost:8000/** (Garba hero with `12 OCT` badge + registration form) and
**http://localhost:8000/admin** (operations dashboard — live DB counts, Garba KPI prominent).

## 5. How to use it (the experiments)

```bash
make demo-rsync       # Scenario A (~30 s): snapshot → 20 HTTP regs → DELETE → restore → 100/20
make demo-pgbackrest  # Scenario B (~60 s): full backup → 20 regs → restore point → DELETE → PITR → 120/40
make benchmark        # Exp 2+3 (~40 s): 20k-row full→diff→incr + pg_dump comparison
make compare          # regenerate charts from the CSVs (never hand-typed numbers)
make report           # charts + DOCX report + PPTX deck
make clean            # tear down volumes (wipes lab data)
```

During any scenario, refresh `/admin` in the browser: you will see baseline → 120 → Garba 0
(incident) → recovered counts, all from live PostgreSQL. Scenario scripts assert every
invariant and abort with a useful message instead of faking success; each run appends to
`results/experiment_runs.csv` under its own `--run-id` (run1/run2 already recorded).

To run the full backup manually: `docker compose exec -T db su postgres -c "pgbackrest
--stanza=stagepass --type=full backup"`, then `… info` to inspect it.

## 6. Repository map

- `app/` — FastAPI + Jinja2 (`main.py`, `db.py` with restore-resilient connections, `templates/`, `static/`)
- `docker/` — DB/app/tools images, `pgbackrest.conf` (stanza `stagepass`), PG archiving tuning, init SQL
- `sql/` — `schema.sql`, deterministic `seed.sql`, controlled `incident.sql`, `verify.sql`, `reset.sql`
- `scripts/` — `workload.py` (deterministic HTTP regs), `scenario_rsync.py`, `scenario_pgbackrest.py`,
  `benchmark.py`, `compare.py` (charts), `build_report.py` / `build_pptx.py`, `safety.py`, `common.py`
- `tests/` — API, seed-idempotency and safety-guard regression tests
- `docs/` — plan, `API.md`, `EXPERIMENT_PROTOCOL.md`, **`RESULTS.md`**, `DEMO_RUNBOOK.md`,
  `SOURCES.md`, full report (`.docx` + `.md` source), slide deck (`.pptx`), speaker + video scripts
- `results/` — raw CSVs/JSON, `logs/` (incl. DB recovery-target evidence + retention demo),
  `plots/` (generated charts), `screenshots/` (genuine headless-Chromium captures)

## 7. Safety & limits (read before demoing)

Destructive scripts require `STAGEPASS_LAB=1`, validate every source/destination path, refuse
host paths and unknown targets, and log everything. No destructive app endpoints exist and the
app never sees the Docker socket. Honest limits: the repo is laptop-local (no off-host disk
protection), bench trials are single-run, and any PITR target discards transactions after it —
see `docs/RESULTS.md` §RTO/RPO and the report's *Threats to validity*.

## 8. Troubleshooting

- `db` unhealthy: `docker compose logs db` (archive-push errors *before* `stanza-create` are normal).
- Dashboard 500: fixed GROUP BY regression is in `app/main.py` — rebuild with
  `docker compose up -d --build app`.
- PITR refuses to run: required WAL not yet archived — check `pg_stat_archiver`, rerun the scenario.
- Port clash: app `:8000`, db `:5433`. Low disk: `docker system prune`, or
  `python3 scripts/benchmark.py --rows 5000`.
- Full references with claim mapping: `docs/SOURCES.md` (pgbackrest.org + postgresql.org docs).
