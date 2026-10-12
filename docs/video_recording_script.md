# Video Recording Script (chronological, one full take + contingency)

## Pre-recording checklist
- [ ] `docker compose ps` — db/app healthy; `make test` 8/8 green.
- [ ] `make seed` → SQL 100/20 confirmed; `/admin` shows 100/20 (bench table may add rows — reseed first).
- [ ] Prior run1/run2 evidence intact in `results/` (CSVs, logs, plots, screenshots).
- [ ] Restored-target LSNs noted: run1 `0/1100BE00`, run2 `0/1A00CC28` (report on demand).
- [ ] Open: PPT (slide 1), browser tabs `/` + `/admin`, two terminals (one for commands, one for `docker compose logs db -f`).
- [ ] Hide secrets/private tabs; no internet needed while recording; clean reset ready (`--run-id video-take1`).
- [ ] Record timings on camera; never show a stale dashboard — refresh on screen after every state change.

## Take 1 (≈10 min)
0:00 (PPT 1–2) Say: “PostgreSQL disaster recovery with pgBackRest — can we survive an accidental
mass DELETE on KJSCE Garba Eve, 12 October?”
0:45 (browser `/`) Scroll hero (12 OCT badge, Register Now). “Real app, real database.”
1:30 (`/admin`) “Baseline: 100 bookings, 20 Garba — live SQL counts.”
2:00 (terminal) `make demo-rsync` — narrate snapshot → workload (20×200) → incident.
3:00 (browser) Refresh `/admin`: Garba 0. “The incident is real.”
3:30 (terminal) Let restore finish; refresh `/admin`: 100/20. “Snapshot time — the 20 new IDs are gone.”
4:30 (terminal) `docker compose exec -T db su postgres -c "pgbackrest --stanza=stagepass info"` — point at full backup label.
5:00 `make demo-pgbackrest` — narrate restore point + “waiting for WAL archival” lines.
6:00 Refresh `/admin` at incident (Garba 0), then after promote: 120/40. “All twenty back.”
7:00 (terminal) `grep -i "recovery target" results/logs/pgbackrest-run2-db-recovery.log` — “PostgreSQL confirms the target.”
7:30 Show `results/plots/recovery_counts.png` + `backup_durations.png`. Read conclusion sentence.
8:30 (PPT 11–12) Limitations + references + `make` reproduction commands. Stop.

## Contingency (if any step fails on camera)
1. Keep recording 10 s, read the error aloud. 2. Show the matching passing evidence from
run1/run2 (`experiment_runs.csv`, saved logs). 3. Fix off-camera, then record a clean insert
shot of only the failed step with the same `--run-id video-take2`. 4. Never splice a simulated
success — label every insert (“re-recorded step, same script, new run ID”).
