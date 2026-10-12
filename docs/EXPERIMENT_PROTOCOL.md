# Experiment Protocol (exact, repeatable)

Environment: `docker compose up -d --build` (db healthy before app via healthchecks).
Lab guard: every destructive script requires `STAGEPASS_LAB=1` and a `stagepass`
database URL, validates rsync paths, refuses unknown/host paths, logs, non-zero exit on failure.

## Common dataset
`make seed` (or scenario reset): `sql/reset.sql` → `schema.sql` → `seed.sql`.
Invariants: total bookings = 100 (20 Garba / 50 Maker / 30 Cinema), ids `bk_seed_001..100`.

## Scenario A — snapshot-only rsync without archived WAL (`make demo-rsync`)
1. Reset, assert 100/20.
2. `compose stop db`; `backup-tools: rsync -aHAX --delete PGDATA/ /snapshots/rsync-baseline/`; manifest (scenario, dataset, timestamp, counts, versions) OUTSIDE PGDATA; `compose start db`; assert 100/20.
3. `workload.py --count 20 --batch <batch>` (deterministic `attendee1NN@example.test`); require 20/20 HTTP 200; assert 120/40.
4. Incident: `sql/incident.sql` (DELETE Garba bookings by slug); record affected rows; assert Garba = 0.
5. Stop db; guarded `rsync --delete` restore; start db; wait healthy; assert 100/20 and 0/20 batch rows remain. Log to `results/experiment_runs.csv`. Expected: 20 post-snapshot rows LOST (snapshot-time recovery, NOT PITR).

## Scenario B — pgBackRest + WAL + named PITR (`make demo-pgbackrest`)
1. Wipe lab repo; reset seed 100/20; `stanza-create`; `check` must succeed (capture output).
2. `--type=full backup`; `info` (record label/time/size).
3. Same workload (different batch); assert 120/40.
4. `pg_create_restore_point(stagepass_before_incident_<run>)` → record LSN/time; `pg_switch_wal()`; POLL until `last_archived_wal >=` restore-point WAL file AND file present under `archive/.../<timeline>/`; abort on timeout or NEW archiver failures.
5. Same incident; assert Garba = 0; record incident time.
6. Stop db; clean PGDATA contents (exact-path guarded, documented pgBackRest requirement); `restore --type=name --target=<point> --target-action=promote` (via backup-tools, since exec needs a running container); start db; confirm recovery-target evidence in db logs.
7. SQL verify: 120/40, 20/20 batch ids, 0 orphans; refresh UI. Expected: DELETE absent (target precedes it), all legit WAL-represented transactions preserved.

## Experiment 2 — backup modes (`make benchmark`, resource-tunable `--rows`, default 20000)
Separate `bench_payload` table: full → mutate ~5% (`id%20=0`) → diff → mutate (`id%20=7`) → incr. Record duration, `info` sizes, repo bytes. Sizes are pgBackRest-reported compressed repo bytes vs `pg_total_relation_size`; never conflated. Optional `--with-dump`: `pg_dump -Fc` + `pg_restore --clean` timing (selective restore yes, WAL replay no-by-itself).

## Experiment 4 — verification & retention
`check` before restore; `info` inspection; `expire --repo1-retention-full=1` in lab repo only (see `results/logs/pgbackrest-expire-demo.txt`). Never expire the only usable backup before its scenario.

## Timings
RTO component times (backup/restore/app-ready durations in `experiment_runs.csv`); RTO = recovery-start → verified usable service. RPO discussed separately (target achieved; production RPO depends on archive lag/config — no zero-RPO claim).

## Reproducibility
Each scenario rerun with a new `--run-id` (run1 + run2 recorded, separate batches); earlier rows preserved in CSVs.
