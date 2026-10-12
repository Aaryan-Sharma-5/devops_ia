# Demo Runbook (7–10 min live)

Pre-check (do once, before audience): `docker compose ps` (all healthy),
`make test` green, both scenarios passed at least once, screenshots in
`results/screenshots/`. Keep a terminal + browser (PPT, `/`, `/admin`) ready.
No internet needed during demo. Lab only: `STAGEPASS_LAB=1`.

## A. Set the scene (1 min, PPT)
Accidental `DELETE` of Garba bookings; question: snapshot-only vs pgBackRest+WAL.

## B. Baseline in browser (1 min)
Open `/admin`: 100 total / 20 Garba (run `make seed` first if bench data present).
SQL proof: `SELECT COUNT(*) FROM bookings` → 100.

## C. Scenario A (2 min)
`make demo-rsync` (or pre-recorded log + live `results/experiment_runs.csv` row):
snapshot → 20 regs → incident (refresh `/admin`: Garba 0) → restore → refresh:
100/20, 20 new IDs missing. State: snapshot time, NOT PITR.

## D. Scenario B (3 min)
`pgbackrest --stanza=stagepass info` (full backup) → archiver check →
restore-point LSN → same 20 regs → incident → `restore --type=name
--target=<point> --target-action=promote` → `docker compose logs db`
("recovery target" evidence) → refresh `/admin`: 120/40, new IDs present.

## E. Numbers + close (1–2 min)
`results/plots/recovery_counts.png`, `backup_durations.png`, comparison table
(`docs/RESULTS.md`): PITR ≈ +5s RTO, +20 transactions; diff/incr ≈ 15% of full
bytes. Limitations: laptop repo, single trials, target choice discards later data.

## Fallback
If a live restore overruns: show the completed run1/run2 CSV rows + saved
`results/logs/*-db-recovery.log` + screenshots; never present diagrams as live output.
Reset anytime: scenario scripts are idempotent per `--run-id`.
