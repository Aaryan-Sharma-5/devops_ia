# Presentation + Live Demo Script (slide-by-slide, ~15 min talk + 7–10 min demo)

Topic: “Automated PostgreSQL Backup and Point-in-Time Recovery using pgBackRest”
Focus statement: “This project demonstrates how pgBackRest automates PostgreSQL database backups, WAL archiving, and disaster recovery. It explores restoring a database to a specific point in time after accidental data loss, evaluating recovery time and reliability without requiring cloud infrastructure.”

## Slide 1 — Title (1 min)
Say: “Good morning. Our project explores Automated PostgreSQL Backup and Point-in-Time Recovery using pgBackRest.
We demonstrate how pgBackRest automates database backups, WAL archiving, and disaster recovery without requiring
cloud infrastructure, demonstrated through StagePass—an event-registration platform whose flagship event is
KJSCE Garba Eve on 12 October. Everything runs locally on Docker Compose: PostgreSQL 17.11 with pgBackRest 2.59.3.”
Point at: version line. Terms: WAL = write-ahead log, every change recorded first.
No switch yet.

## Slide 2 — Problem (1.5 min)
Say: “Imagine peak registrations, and someone runs a DELETE that wipes every Garba Eve
booking. Eighty bookings remain, Garba reads zero, and the operations dashboard visibly
breaks. Our requirement: bring the service back and lose as few legitimate registrations
as possible — then measure what each strategy costs.”
ACTION: switch to browser `/admin` showing recovered 120/40 state; say “this dashboard
reads live PostgreSQL — I’ll break it and fix it in front of you.”

## Slide 3 — What the evaluator sees (1 min)
Say: “Forty Garba bookings, 120 total, recent IDs — all queried fresh on each load. Nothing
here is hardcoded; after each recovery I refresh this exact page.”
SQL proof (terminal): `SELECT COUNT(*) FROM bookings;` → 120.

## Slide 4 — Research question & objectives (1 min)
Read the question aloud. Map O1→slides 6–8, O2→slides 9–10, O3→slides 7/10.
Back to PPT.

## Slide 5 — Why snapshot-only is limited (1.5 min)
Say: “A stopped-cluster rsync mirror is perfectly consistent — at time T. But our baseline
deliberately replays no WAL, so anything after T is unrecoverable. To be fair: rsync plus a
WAL strategy could do more; we test snapshot-ONLY versus pgBackRest-plus-WAL.”
Terms: PITR = replaying history to a chosen moment.

## Slide 6 — Architecture (1.5 min)
Trace: browser → FastAPI → PostgreSQL; WAL segments → archive-push → repo volume (separate
from PGDATA so a restore never eats its own recovery copy); backup-tools runs guarded ops.
Note the app uses short-lived DB connections, so it survives the seconds the DB is down.

## Slide 7 — Backup modes + named PITR (1.5 min)
Say: “Full 10.6 seconds and 4.5 MB; differential 2.5 seconds and under 0.7 MB; incremental
3 seconds. Those sizes are compressed repository bytes — I never compare them with raw
database megabytes as if equal. For recovery we plant a named flag in the WAL before the
incident and restore to that name — and we refuse to restore until that WAL segment is
proven archived. One of our runs actually aborted on that guard, which is the guard working.”

## Slide 8 — StagePass controls (1 min)
ACTION: show `/` homepage: 12 OCT badge, Register Now, live pill.
Say: “Seed is always 100 bookings; both scenarios receive the identical 20 HTTP registrations.”

## Slide 9 — Scenario A result (2 min + optional live `make demo-rsync`)
Say: “Snapshot, 20 registrations, DELETE, restore: back to 100, Garba 20, zero of the new
twenty survive. Correct — and lossy. Reproduced twice.”
ACTION (if time): run `make demo-rsync`, refresh `/admin` mid-incident (Garba 0) and after
(20). Else show `results/experiment_runs.csv` rsync rows + recovery chart.

## Slide 10 — Scenario B result (2.5 min + optional live PITR)
Say: “Full backup, same 20 registrations, named restore point with recorded LSN, verified
archival, same DELETE — then restore to the name and promote. PostgreSQL logs confirm the
target; the app shows 120 and 40 with all twenty IDs back, twice.”
ACTION: `docker compose logs db | grep -i "recovery target"`; refresh `/admin`.
Contrast: “pg_dump took 0.3 seconds but cannot replay WAL by itself — different tool, different job.”

## Slide 11 — Evaluation & conclusion (1.5 min)
Say: “RTO differs by seconds — eleven to fifteen versus eighteen to twenty-one. Recoverability
differs by twenty transactions. Limits, honestly: laptop-local repo, single bench trial,
and any PITR target discards later data. Answer: pgBackRest plus archived WAL moves recovery
from ‘state at backup time’ to ‘state at the target you chose.’”

## Slide 12 — References & close (0.5 min)
Point at pgbackrest.org + postgresql.org docs (accessed 2026-10-12, mapped in SOURCES.md).
Say: “Reproduce it with five make commands — README has them. Happy to re-run either scenario live.”

## Run-of-show timing
PPT 1–8 ≈ 9 min → demo A ≈ 2 min → demo B ≈ 3 min → close ≈ 1 min ≈ 15 min total
(7–10 min core demo = A+B+refreshes). Fallback: pre-recorded `results/logs/` + CSV rows;
label diagrams as diagrams, never as live output.
