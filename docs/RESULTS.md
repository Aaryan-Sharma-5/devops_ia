# Results (measured 2026-10-12/13; host IST = UTC+5:30)

Versions (see `results/experiment_metadata.json`): PostgreSQL **17.11**
(Debian 17.11-1.pgdg12+2), pgBackRest **2.59.3**, Docker 29.8.1 / Compose 5.5.1,
Arch Linux, 8 CPU. Research question: *How does pgBackRest with archived WAL
improve PostgreSQL recoverability after accidental data loss compared with a
consistent file-system snapshot alone, and what are the time and storage
trade-offs of its backup strategies?*

## Experiment 1 — snapshot-only vs PITR (seed-v1, 20 HTTP regs each)

| run | method | baseline | pre-incident | post-incident (Garba) | recovered | new regs recovered | backup | restore | app-ready |
|---|---|---|---|---|---|---|---|---|---|
| rsync-run1 | snapshot-only, no WAL | 100 | 120 | 80 (0 Garba) | **100** | **0/20 lost** | 1.1s | 15.0s | 15.0s |
| rsync-run2 | snapshot-only, no WAL | 100 | 120 | 80 (0 Garba) | **100** | **0/20 lost** | 0.5s | 10.6s | 10.6s |
| pgbackrest-run1 | full + named PITR | 100 | 120 | 80 (0 Garba) | **120** | **20/20** | 13.3s | 17.6s | 17.6s |
| pgbackrest-run2 | full + named PITR | 100 | 120 | 80 (0 Garba) | **120** | **20/20** | 7.2s | 20.6s | 20.6s |

Raw: `results/experiment_runs.csv`, `results/registration_requests.csv` (80/80 HTTP 200),
`results/logs/pgbackrest-run*-db-recovery.log` (recovery-target evidence), charts
`results/plots/recovery_counts.png`. PITR targets: `stagepass_before_incident_pgbackrest_run1`
(LSN 0/1100BE00, backup 20261012-210053F) and `..._run2` (LSN 0/1A00CC28); repo ≈ 4.8MB
(compressed pgBackRest bytes, NOT raw DB size).

**Interpretation.** Snapshot-only restores to snapshot time (100) and cannot replay the 20
legit post-snapshot transactions — they are lost. Named PITR replays archived WAL to the
verified restore point, returning 120/40 with the incident DELETE absent. This compares a
*snapshot-only strategy* with pgBackRest+WAL; rsync combined with a proper WAL strategy could
do more — that combination was intentionally excluded from the baseline.

## Experiment 2 — backup modes (bench 20,000 rows, `pg_total_relation_size` ≈ 3.9MB)

| type | duration | pgBackRest backup size* | DB size reported |
|---|---|---|---|
| full | 10.6s | 4.5MB | 33.5MB |
| differential (~5% rows changed) | 2.5s | 697.7KB | 33.5MB |
| incremental (another ~5%) | 3.0s | 635.8KB | 33.5MB |

\*compressed repo bytes for this backup (`info`: `results/logs/pgbackrest-info-final.txt`).
5% of SQL rows ≠ 5% of bytes: PostgreSQL writes whole pages and pgBackRest compresses;
diff/incr are ~15%/~14% of the full artifact here, not 5%. Chart: `results/plots/backup_durations.png`.
Single trial (lab constraints); medians need `--trials 3` on a bigger host. One stale full row
(backup 20261012-210804F, from the interrupted benchmark run) was removed from
`backup_benchmarks.csv` and expired from the repo (`pgbackrest-expire-demo.txt`) — documented here.

## Experiment 3 — pg_dump baseline (same logical data, 120 bookings + 20k bench rows)

`pg_dump -Fc`: 0.3s, 507,577 bytes; `pg_restore --clean` to a scratch DB: 1.4s, 120 bookings
verified. Selective restore: yes. WAL replay to a timestamp by itself: no. Logical dumps
complement but do not replace physical PITR.

## Experiment 4 — verification & retention
`check` green before every restore; restore refused until the restore-point WAL segment was
proven archived (one aborted run2 attempt is honest evidence the guard works); `expire
--repo1-retention-full=1` removed only the orphan full backup in the isolated lab repo.

## RTO / RPO
RTO (recovery-start → verified usable app): rsync ≈ 11–15s, PITR ≈ 18–21s on this laptop —
PITR costs a few seconds more and returns 20 more transactions. RPO: lab target achieved
exactly (restore point after all 20 regs, before DELETE); production RPO depends on archive
lag/monitoring — never zero. Laptop-local repo ≠ off-host DR; restore-target choice discards
later transactions; results need required backups+WAL retained.

## Deviations (all fixed, evidence kept)
Seed CTE visibility bug (0 rows first run) → split statements; dashboard GROUP BY bug → fixed +
regression test; restore-via-stopped-container → backup-tools path; data-dir clean step added;
timeline-1 hardcode → dynamic (run2 abort proved the guard); benchmark `%%` typo → fixed.
