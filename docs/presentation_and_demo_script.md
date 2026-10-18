# Presentation & Live Demo Script (10–12 min presentation + 5–7 min core demo)

Topic: “Automated PostgreSQL Backup and Point-in-Time Recovery using pgBackRest”
Focus statement: “This project demonstrates how pgBackRest automates PostgreSQL database backups, WAL archiving, and disaster recovery. It explores restoring a database to a specific point in time after accidental data loss, evaluating recovery time and reliability without requiring cloud infrastructure.”

## Slide 1 — Title (1 min)
Say: “Good morning. Our project explores Automated PostgreSQL Backup and Point-in-Time Recovery using pgBackRest,
presented by Aaryan Sharma (16010123012), Anamay Narkar (16010123040), Aditya Singh (16010123025), and Vraj Soni (160101220).
We demonstrate how pgBackRest automates database backups, WAL archiving, and disaster recovery without requiring
cloud infrastructure, demonstrated through StagePass—an event-registration platform whose flagship event is
KJSCE Garba Eve on 12 October. Everything runs locally on Docker Compose: PostgreSQL 17.11 with pgBackRest 2.59.3.”
Point at: version line and team roll numbers. Terms: WAL = write-ahead log, every transactional change recorded first.

## Slide 2 — Problem (1.5 min)
Say: “Imagine peak registrations, and someone runs an accidental DELETE that wipes every Garba Eve
booking. Eighty bookings remain, Garba reads zero, and the operations dashboard visibly breaks.
Target: recover all 20 post-backup registrations in this test without losing referential integrity,
and evaluate what each disaster recovery strategy costs in recovery time and data loss.”
ACTION: Switch to browser `/admin` showing recovered 120/40 state; say “this dashboard reads live PostgreSQL relations on every load.”

## Slide 3 — What the evaluator sees (1 min)
Say: “Forty Garba bookings, 120 total, recent attendee IDs — all queried fresh from PostgreSQL relations on each request.
Nothing here is hardcoded or mocked; after each recovery run, we refresh this exact page to observe database state.”
SQL verification command: `SELECT COUNT(*) FROM bookings WHERE simulation_batch_id='pbr-post-backup';` → 20.

## Slide 4 — Research question & objectives (1 min)
Read the question aloud. Map:
- Objective 1 (Automated Lab) → Slides 6 & 8
- Objective 2 (Zero-Cloud DR) → Slides 9 & 10
- Objective 3 (Recovery Time & Reliability) → Slides 7 & 11

## Slide 5 — Physical Snapshot vs WAL Replay (1.5 min)
Say: “A stopped-cluster rsync mirror is perfectly consistent — at snapshot moment T. But our baseline
deliberately replays no WAL, so the 20 registrations created after T are unrecoverable.
To be fair: rsync combined with an external WAL replay design could do more; our test specifically evaluates
snapshot-ONLY versus pgBackRest-plus-WAL. pgBackRest shifts disaster recovery from 'state at the last backup'
to 'recovery to a named restore point recorded in WAL'.”

## Slide 6 — Architecture (1.5 min)
Trace: Browser → FastAPI (`:8000`) → PostgreSQL 17.11 (Host `:5433`, Container `:5432`).
PostgreSQL pushes 16 MB WAL segments via `archive_command` to the isolated volume `/var/lib/pgbackrest`.
The backup repository is strictly separated from `PGDATA` so restore operations never risk overwriting backup archives.
`backup-tools` sidecar coordinates guarded snapshot and restore CLI commands.
Note: FastAPI uses request-scoped database sessions, surviving cleanly when PostgreSQL restarts during recovery.

## Slide 7 — Backup modes + named PITR (1.5 min)
Say: “In our single-trial benchmark: Full took 10.6 s, Differential took 2.5 s, and Incremental took 3.0 s.
Storage distinction: Individual backup sets measured 4.5 MB for Full, 697.7 KB for Differential, and 635.8 KB for Incremental.
Cumulative repository total grew from 12.1 MB to 14.3 MB and 16.3 MB. Differential and incremental modes cut routine backup storage by >84%.
For disaster recovery, we plant a named restore point in WAL: `stagepass_before_incident_pgbackrest_run2`.
Our harness verifies the required WAL segment exists in `/var/lib/pgbackrest/archive/` and checks timeline ordering before allowing restore.”

## Slide 8 — StagePass controls & repeatability (1 min)
Show homepage `/`: 12 OCT badge, Register Now modal, live operations status pill.
Say: “Deterministic 100-row seed; identical 20 HTTP POST registrations via `scripts/workload.py`; repeated across Run 1 and Run 2.”

## Slide 9 — Scenario A result (Snapshot Baseline) (1.5 min)
Say: “Snapshot taken at 100 bookings. 20 registrations arrive (count 120). Unbounded DELETE wipes Garba.
Rsync snapshot restored: database returns to 100 bookings, Garba 20. Exactly zero of the 20 new registrations survived.
The baseline snapshot deliberately has no WAL replay mechanism. Recovery took 15.0 s in Run 1 and 10.6 s in Run 2.”

## Slide 10 — Scenario B result (pgBackRest PITR) (2 min)
Say: “Full backup taken at 100 bookings. Same 20 registrations arrive. Named restore point `stagepass_before_incident_pgbackrest_run2` planted.
Archival gate confirms segment on disk. Unbounded DELETE wipes Garba.
pgBackRest restores the base physical backup and replays WAL forward to the restore point target.
PostgreSQL engine recovery log explicitly records: `recovery stopping at restore point \"stagepass_before_incident_pgbackrest_run2\"`.
All 120 bookings, 40 Garba, and 20 new registrations recovered intact.
Recovery Time (RTO): 17.6 s in Run 1 and 20.6 s in Run 2 (observed deltas of +2.6 s and +10.0 s over snapshot).
Key qualification: This experiment achieved zero loss of the 20 tested registrations; production RPO depends on WAL archival lag and retention.”

## Slide 11 — Quantitative Evaluation & Benchmarks (1 min)
Say: “Point at the comparison plots from real CSVs.
RTO observed differences were 2.6 s and 10.0 s to achieve complete transaction recovery.
Storage chart distinguishes individual backup delta from cumulative repository total.
Single trial limitation: benchmark represents one measured run, not a multi-trial median.”

## Slide 12 — Conclusion & Questions (0.5 min)
Say: “In both recorded PITR trials, all 20 post-backup registrations were recovered by restoring to the verified pre-incident named restore point.
Zero loss of the 20 tested registrations was achieved without cloud infrastructure.
All results, scripts, and logs are in the repository and reproducible via Makefile.”

## Timing and Run-of-Show
- Presentation (Slides 1–12): 10–12 minutes
- Live Core Demonstration (Admin inspection + PITR recovery log verification): 5–7 minutes
- Fallback: Saved evidence in `results/logs/pgbackrest-run2-db-recovery.log` and `results/experiment_runs.csv`
- Total Evaluator Budget: 15–18 minutes
