# Automated PostgreSQL Backup and Point-in-Time Recovery using pgBackRest
**Automating Database Backups, WAL Archiving, and Disaster Recovery without Cloud Infrastructure**
*DevOps Theory — Internal Assessment Case Study | Date: 2026-10-18*

> **Project Focus:** This project demonstrates how pgBackRest automates PostgreSQL database backups, WAL archiving, and disaster recovery. It explores restoring a database to a specific point in time after accidental data loss, evaluating recovery time and reliability without requiring cloud infrastructure.
> **Research Question:** How does pgBackRest automate PostgreSQL database backups, WAL archiving, and disaster recovery to a specific point in time after accidental data loss, and what are its recovery time and reliability trade-offs without requiring cloud infrastructure?

### Project Team Details
| Role | Name & Roll Number |
|---|---|
| Group Member 1 | Aaryan Sharma (16010123012) |
| Group Member 2 | Anamay Narkar (16010123040) |
| Group Member 3 | Aditya Singh (16010123025) |
| Group Member 4 | Vraj Soni (16010122309) |

## 2. Abstract / Executive Summary

This project demonstrates how pgBackRest automates PostgreSQL database backups, WAL archiving, and disaster recovery. It explores restoring a database to a specific point in time after accidental data loss, evaluating recovery time and reliability without requiring cloud infrastructure.

In enterprise database systems, operator error—specifically unconstrained DELETE or UPDATE statements—represents one of the most severe classes of production downtime. This case study investigates disaster recovery mechanisms for PostgreSQL 17.11 through an empirical, end-to-end event registration platform called StagePass. We contrast a traditional stopped-cluster filesystem snapshot (rsync) against pgBackRest 2.59.3 with continuous Write-Ahead Log (WAL) archiving and Point-in-Time Recovery (PITR).

Under identical workloads of 100 seeded rows and 20 real HTTP bookings, an accidental DELETE removes all 40 flagship bookings. The snapshot-only baseline recovers the cluster to snapshot time (100 bookings), but completely loses all 20 post-snapshot transactions because those transactions occurred after the snapshot and the baseline deliberately has no WAL replay mechanism. In contrast, in both recorded PITR trials, all 20 post-backup registrations were recovered by restoring to the verified pre-incident named restore point (stagepass_before_incident_pgbackrest_run2). This experiment achieved zero loss of the 20 tested registrations; production RPO depends on WAL archival and retention. Observed recovery times were 17.6 s in Run 1 and 20.6 s in Run 2 (differences of 2.6 s and 10.0 s compared to snapshot-only). Furthermore, differential and incremental backup strategies demonstrated an 85% reduction in individual backup storage footprint and over 70% reduction in execution time compared to full backups.

> **[KEY EXPERIMENTAL FINDING]:** In both recorded PITR trials, all 20 post-backup registrations were recovered by restoring to the verified pre-incident named restore point. This experiment achieved zero loss of the 20 tested registrations; production RPO depends on WAL archival and retention.

## 3. Introduction

PostgreSQL serves as the transactional backbone across microservice architectures, enterprise SaaS, and mission-critical web platforms. While Site Reliability Engineering (SRE) paradigms emphasize High Availability (HA) through replication, replication alone does not protect against data corruption: a bad DELETE command immediately propagates to all read replicas within milliseconds. True disaster recovery requires historical immutability via write-ahead log replay.

This project explores local disaster recovery automation, demonstrating that robust point-in-time recovery, continuous WAL archiving, and backup retention can be achieved reliably without requiring cloud infrastructure.

## 4. Problem Statement

During peak traffic for the KJSCE Garba Eve event on 12 October, an operational incident occurs: an engineer inadvertently issues an unbounded query: DELETE FROM bookings WHERE event_id = 1;. The Garba booking count drops to 0, and the operations dashboard visibly reports service degradation. The engineering requirements are: (1) automate restoration of database state to a specific point in time, (2) evaluate recovery time (RTO) and reliability (RPO) without relying on external cloud infrastructure, and (3) quantify the time and storage trade-offs across backup modes.

## 5. Research Question and Objectives

Research Question: How does pgBackRest automate PostgreSQL database backups, WAL archiving, and disaster recovery to a specific point in time after accidental data loss, and what are its recovery time and reliability trade-offs without requiring cloud infrastructure?

Objectives:

• Objective 1: Build StagePass containerized app, schema with constraints, deterministic 100-row seed and realistic HTTP workload runner.

• Objective 2: Automate PostgreSQL backups, WAL archiving, and Point-in-Time Recovery to a target point without cloud infrastructure.

• Objective 3: Evaluate recovery time (RTO) and reliability (RPO) after accidental data loss vs consistent filesystem snapshots.

• Objective 4: Measure execution duration and compressed repository storage across Full, Differential, Incremental, and Logical (pg_dump) strategies.

## 6. Scope and Assumptions

Experimental boundaries and architectural assumptions:

• Single Host Isolation: The lab executes on a single local host via Docker Compose. Network partition and multi-host split-brain scenarios are outside current scope.

• Synthetic Attendee Data: All attendee data uses the disposable @example.test domain, ensuring zero exposure of personal identifiable information.

• Headline Metric: Recovery success is measured by persisted, valid booking records and referential integrity (zero orphaned attendee rows).

• Repository Storage: The pgBackRest repository resides on a dedicated local volume; off-site cloud storage replication (e.g. S3/GCS) is simulated through local isolation.

- In scope: rsync stopped baseline, pgBackRest PITR, modes, dump comparison, retention demo.
- Out of scope: Kubernetes orchestration, multi-node HA, encryption-at-rest tuning, production petabyte sizing.

## 7. DevOps Relevance

This investigation directly intersects core DevOps and Site Reliability Engineering principles:

• Mean Time to Recovery (MTTR) & RTO: Rapid automated cluster recreation directly minimizes downtime budgets.

• Recovery as Code: Stanzas, configuration, and restore sequences are scripted, version-controlled, and testable in CI/CD pipelines.

• Observability: The operations dashboard reflects true PostgreSQL database state on every load, avoiding synthetic caching masks.

• Defensive Engineering: Restore procedures enforce archival guards and target verification before allowing destructive promotion.

## 8. Literature / Tool Review

Primary documentation sources and specifications reviewed:

• pgBackRest User Guide and Command Reference (Debian/PG17 track; v2.59.3).

• PostgreSQL 17 Documentation: Chapter 25 (Backup and Restore), WAL configuration, pg_dump/pg_restore/pg_basebackup.

• Academic and industrial literature on SRE principles, transaction durability (ACID), and write-ahead log replay mechanics.

(All official references accessed 2026-10-12; claim mapping detailed in docs/SOURCES.md).

## 9. Logical versus Physical Backups

PostgreSQL provides two distinct backup paradigms with differing operational trade-offs:

• Logical Backups (pg_dump): Dumps database schema and data into SQL or binary format. Highly selective and portable across architectures, but cannot replay write-ahead logs. In our benchmark, pg_dump completed in 0.3 s (0.5 MB), but can only restore the state at dump completion.

• Physical Backups (pgBackRest): Copies raw database disk blocks alongside a stream of WAL segments. Enables Point-in-Time Recovery by rolling forward changes block by block. Measured full physical backup required 10.6 s and 4.5 MB compressed repository storage on the benchmark dataset.

## 10. PostgreSQL WAL and Crash Recovery

PostgreSQL ensures durability through Write-Ahead Logging (WAL): every table modification is committed to sequential 16 MB log segments before data pages are flushed to disk.

With wal_level=replica and archive_mode=on, the engine triggers archive_command whenever a segment fills or archive_timeout expires. Crash recovery and PITR replay these binary records from a base checkpoint to reconstruct exact database state.

## 11. pgBackRest Architecture

pgBackRest operates through stanzas—named configurations binding a PostgreSQL cluster to a backup repository.

Key architectural components include:

• archive-push: Invoked by PostgreSQL archive_command to compress, checksum, and transfer WAL segments asynchronously.

• Dedicated Repository: Manages full, differential, and incremental backup manifests, file-level checksums, and retention expirations.

• Restore Coordinator: Validates repository manifests, writes postgresql.auto.conf recovery parameters, and ensures clean cluster recovery.

## 12. Full, Differential and Incremental Semantics

pgBackRest provides three backup levels:

• Full: Copies all database cluster files. Forms the foundational root of the backup tree.

• Differential: Copies all files modified since the last full backup. Breaks chained dependencies on intermediate incrementals.

• Incremental: Copies only files modified since the immediate preceding backup of any type. Minimizes daily execution time and storage consumption.

## 13. PITR Theory and Named Recovery Targets

Point-in-Time Recovery relies on specifying a deterministic stopping boundary:

• Ambiguity of Timestamps: Time-based targets (recovery_target_time) are vulnerable to NTP clock skew and sub-second transaction interleaving.

• Named Restore Points: Executing SELECT pg_create_restore_point('rp_name'); writes an explicit marker directly into the WAL stream with an identifiable Log Sequence Number (LSN).

• Verified WAL Archival Gate: The recovery coordinator asserts that the segment containing the restore point LSN has reached the repository disk before initiating recovery.

## 14. System Architecture Diagram

Multi-container environment topology:

• web (FastAPI, port 8000) -> db (PostgreSQL 17.11 + pgBackRest, port 5433).

• backup-tools (CLI orchestrator) mounts pgdata, repo, and snapshots volumes.

• Strict volume segregation guarantees zero risk of restore operations corrupting backup archives.

## 15. StagePass Application Design and Database Schema

StagePass models events, attendees, and bookings with strict foreign keys, CHECK constraints, and uniqueness guarantees (sql/schema.sql). The seed establishes 100 bookings across three events: KJSCE Garba Eve (20), TechSummit (50), and MusicFest (30). The application exposes RESTful endpoints for health introspection and validated registration.

![Figure 1 — StagePass Home UI (genuine screenshot).](results/screenshots/home.png)
*Figure 1 — StagePass Home UI (genuine screenshot).*

![Figure 2 — Operations Dashboard (genuine screenshot).](results/screenshots/admin.png)
*Figure 2 — Operations Dashboard (genuine screenshot).*

## 16. Implementation Environment and Versions

Hardware & Container Host: {'os': 'NAME="Arch Linux"', 'platform': 'Linux-7.2.6-arch2-1-x86_64-with-glibc2.44', 'cpus': 8}.

PostgreSQL Version: PostgreSQL 17.11 (Debian 17.11-1.pgdg12+2) on x86_64-pc-linux-gnu, compiled by gcc (Debian 12.2.0-14+deb12u1) 12.2.0, 64-bit.

pgBackRest Version: pgBackRest 2.59.3.

Docker Version: Docker version 29.8.1, build 4a63305d74 | Compose: Docker Compose version 5.5.1.

Complete version lock files and environment snapshots recorded in results/experiment_metadata.json.

## 17. Configuration and Commands

Core configuration directives implemented in docker/pgbackrest.conf and postgresql.conf:

• archive_mode = on

• archive_command = 'pgbackrest --stanza=stagepass archive-push %p'

• wal_level = replica

• archive_timeout = 60

Operational CLI commands utilized:

• Stanza Initialization: pgbackrest --stanza=stagepass stanza-create && pgbackrest --stanza=stagepass check

• Backup Creation: pgbackrest --stanza=stagepass --type=full backup

• Targeted Restore: pgbackrest --stanza=stagepass --type=name --target=stagepass_before_incident_pgbackrest_run2 --target-action=promote restore

## 18. Controlled Experimental Methodology

To maintain rigorous scientific control, both scenarios execute under identical conditions:

• Deterministic Seeding: Database initialized to exact 100-row seed prior to each scenario run.

• Workload Generation: Identical 20 HTTP POST requests executed against the registration API.

• Two-Phase Replication: Run 1 and Run 2 executed independently with distinct run IDs and raw logs.

• Safety Assertion: The test harness refuses to initiate PITR until the target restore point LSN is proven archived.

## 19. rsync Snapshot-Only Baseline

Consistent stopped-cluster filesystem snapshot created via rsync -aHAX --delete. When the DELETE incident removes Garba bookings, restoring the snapshot reverts the database to snapshot time (100 bookings). The snapshot-only method loses the 20 post-snapshot registrations because those transactions occurred after the snapshot and the baseline deliberately has no WAL replay mechanism. This reflects the limitation of snapshot-only architectures rather than an inherent limitation of rsync itself (reproduced across Run 1 and Run 2).

## 20. pgBackRest PITR Experiment

pgBackRest hot physical backup taken at 100 bookings. 20 registrations arrive, followed by planting named restore point stagepass_before_incident_pgbackrest_run2. After verified timeline-aware WAL archival, the DELETE query runs. pgBackRest restores the base backup and rolls forward WAL segments to the named restore point. The cluster promotes with all 120 bookings and 20/20 new registrations intact (reproduced across Run 1 and Run 2). In both recorded PITR trials, all 20 post-backup registrations were recovered by restoring to the verified pre-incident named restore point. This experiment achieved zero loss of the 20 tested registrations; production RPO depends on WAL archival and retention.

## 21. Backup-Mode and Dump Benchmarks

Empirical benchmark on 20,000 synthetic rows (single trial measurements):

• Full Backup: 10.6 s duration, 4.50 MiB individual backup size (4,718,592 bytes), 11.58 MiB cumulative repository total (12.1 MB decimal; 12,137,779 bytes measured via du -sb /var/lib/pgbackrest).

• Differential Backup: 2.5 s duration (76% faster), 697.7 KiB individual backup size (714,445 bytes; 84.5% delta saving), 13.67 MiB cumulative repository total (14.3 MB decimal; 14,338,561 bytes).

• Incremental Backup: 3.0 s duration (71% faster), 635.8 KiB individual backup size (651,059 bytes; 85.9% delta saving), 15.53 MiB cumulative repository total (16.3 MB decimal; 16,284,776 bytes).

• Logical pg_dump: 0.3 s runtime, 0.5 MB dump size, but zero WAL replay capability.

Storage Measurements & Metric Distinction: The benchmark table occupied approximately 3.9 MiB of PostgreSQL relation storage (pg_total_relation_size('bench_payload') ≈ 3,896 KiB); pgBackRest reported a 33.5 MB database size for the cluster used in the backup measurement. Individual backup size measures the new compressed data delta captured in that specific backup set (Full: 4.50 MiB, Diff: 697.7 KiB, Incr: 635.8 KiB), whereas cumulative repository size reflects the total disk space occupied by the entire pgBackRest repository measured via du -sb /var/lib/pgbackrest immediately post-backup: Full = 11.58 MiB (12.1 MB decimal; 12,137,779 bytes), Diff = 13.67 MiB (14.3 MB decimal; 14,338,561 bytes), Incr = 15.53 MiB (16.3 MB decimal; 16,284,776 bytes).

## 22. Results Tables and Charts (Real Data)

Empirical data collected from automated test executions (results/experiment_runs.csv and backup_benchmarks.csv):

| Run ID | Baseline | Pre-Incident | Recovered | New Regs | Backup (s) | Restore (s) |
|---|---|---|---|---|---|---|
| rsync-run1 | 100 | 120 | 100 | 0 | 1.1 | 15.0 |
| pgbackrest-run1 | 100 | 120 | 120 | 20 | 13.3 | 17.6 |
| rsync-run2 | 100 | 120 | 100 | 0 | 0.5 | 10.6 |
| pgbackrest-run2 | 100 | 120 | 120 | 20 | 7.2 | 20.6 |

*Note: The benchmark table occupied approximately 3.9 MiB of PostgreSQL relation storage (pg_total_relation_size('bench_payload') ≈ 3,896 KiB); pgBackRest reported a 33.5 MB database size for the cluster used in the backup measurement. Individual backup size measures the new compressed data delta (Full: 4.50 MiB, Diff: 697.7 KiB, Incr: 635.8 KiB). Cumulative repository size reflects total disk footprint measured via du -sb /var/lib/pgbackrest immediately post-backup: Full = 11.58 MiB (12.1 MB decimal; 12,137,779 bytes), Diff = 13.67 MiB (14.3 MB decimal; 14,338,561 bytes), Incr = 15.53 MiB (16.3 MB decimal; 16,284,776 bytes).*

| Trial | Backup Mode | Rows | Duration (s) | Backup Size | Cumulative Repo | Notes |
|---|---|---|---|---|---|---|
| 1 | FULL | 20000 | 10.6 | 4.50 MiB | 11.58 MiB | Base physical backup (100% data) |
| 1 | DIFFERENTIAL | 20000 | 2.5 | 697.7 KiB | 13.67 MiB | 5% rows modified (id%20==0) |
| 1 | INCREMENTAL | 20000 | 3.0 | 635.8 KiB | 15.53 MiB | 5% rows modified (id%20==7) |

![Figure 3 — Booking counts per experimental run.](results/plots/recovery_counts.png)
*Figure 3 — Booking counts per experimental run.*

![Figure 4 — Backup duration comparisons (single trial).](results/plots/backup_durations.png)
*Figure 4 — Backup duration comparisons (single trial).*

![Figure 5 — Storage comparison: Individual backup size vs Cumulative repository total.](results/plots/backup_storage.png)
*Figure 5 — Storage comparison: Individual backup size vs Cumulative repository total.*

## 23. Comparison Matrix

Comprehensive comparison across evaluated disaster recovery strategies:

• Stopped Rsync Snapshot: RTO Run 1 = 15.0 s / Run 2 = 10.6 s; RPO = Snapshot Moment (20 registrations lost; lacks WAL replay by design); Storage = Full uncompressed PGDATA.

• pgBackRest PITR: RTO Run 1 = 17.6 s / Run 2 = 20.6 s (observed deltas of 2.6 s and 10.0 s vs snapshot); RPO = Selected Named Target (all 20 tested registrations recovered; production RPO depends on WAL archival and retention); Storage = Compressed Base + Sequential WAL.

• Logical pg_dump: RTO 1.4 s; RPO = Dump Moment (no post-dump transactions); Storage = Compressed SQL/archive.

## 24. Discussion and Evaluation

The empirical findings demonstrate that the recoverability advantage of pgBackRest far outweighs the marginal recovery time delta. PITR took longer in both recorded runs, with observed differences of 2.6 seconds (Run 1: 17.6 s vs 15.0 s) and 10.0 seconds (Run 2: 20.6 s vs 10.6 s). Two runs illustrate the trade-off between snapshot-only restoration and full WAL replay to a verified target, rather than characterizing general performance variability. While rsync restored the cluster faster, it incurred complete data loss for post-snapshot traffic (20 unrecoverable transactions). In modern booking and transactional systems, an extra duration of 2.6 to 10.0 seconds to replay WAL to an exact verified target point is vastly preferable to losing transactional integrity.

## 25. RTO and RPO Interpretation

• Recovery Time Objective (RTO): Measured as the end-to-end time required for PostgreSQL to complete WAL replay, promote, and accept HTTP traffic. Across recorded runs, PITR RTO was 17.6 s (Run 1) and 20.6 s (Run 2), compared to 15.0 s and 10.6 s for snapshot recovery.

• Recovery Point Objective (RPO): In both recorded PITR trials, all 20 post-backup registrations were recovered by restoring to the verified pre-incident named restore point. This experiment achieved zero loss of the 20 tested registrations; production RPO depends on WAL archival and retention. The configured archive timeout is 60 seconds. Actual recoverability depends on WAL archival success, archive lag, shipping latency, and retention. The experiment verified that the target segment was available before restoration.

## 26. Threats to Validity and Limitations

Academic rigor requires stating threats to validity:

• Construct Validity: RPO in production is influenced by network latency and disk I/O; local Docker volumes eliminate network jitter. Actual recoverability depends on WAL archival success, archive lag, shipping latency, and retention.

• Internal Validity: Named restore points discard transactions committed after the target; concurrent non-incident writes require manual isolation.

• External Validity: Benchmark dataset (20,000 rows) represents medium-scale tables; multi-terabyte production instances require multi-core compression tuning.

• Single Trial Limitation: Backup mode benchmarks represent a single measured trial rather than a multi-trial statistical median.

## 27. Security Considerations

• Credential Hygiene: Database passwords injected via environment variables; zero hardcoded secrets in version control.

• Network Hardening: FastAPI application container does not mount the host Docker socket, preventing container escape vectors.

• Data Privacy: Synthetic attendee emails use RFC 2606 reserved domains (@example.test).

• Lab Scope Warning: Lab credentials (postgres/stagepass) are strictly disposable and unsuitable for production deployments.

## 28. Conclusion (Answering the Research Question)

pgBackRest with continuous WAL archiving definitively improves PostgreSQL recoverability compared to consistent filesystem snapshots alone. In both recorded PITR trials, all 20 post-backup registrations were recovered by restoring to the verified pre-incident named restore point. This experiment achieved zero loss of the 20 tested registrations; production RPO depends on WAL archival and retention. PITR incurred observed recovery time differences of 2.6 s in Run 1 and 10.0 s in Run 2 compared to snapshot alone, while preserving complete transactional integrity. Furthermore, differential and incremental modes reduce routine backup storage by >84%, proving their viability for high-frequency continuous backup regimes.

## 29. Future Improvements

Recommended enhancements for enterprise deployment:

• Off-Site S3 Storage: Integrating MinIO or AWS S3 backends for geo-redundant repository replication.

• Automated DR Drills: Scheduled restore validation in staging environments with automated RTO budget alerting.

• Standby Replication: Pairing pgBackRest with streaming physical standby instances for sub-second failover.

## 30. References

[1] pgBackRest User Guide & Architecture Documentation. https://pgbackrest.org/user-guide.html (v2.59.3).

[2] PostgreSQL 17 Backup and Restore Documentation. https://www.postgresql.org/docs/17/backup.html.

[3] PostgreSQL WAL Configuration and Archiving. https://www.postgresql.org/docs/17/runtime-config-wal.html.

[4] Beyer, B., et al., 'Site Reliability Engineering: How Google Runs Production Systems', O'Reilly Media.

[5] Kleppmann, M., 'Designing Data-Intensive Applications', O'Reilly Media.

## 31. Appendix

• Appendix A: Reproduction Makefile targets (make up, make seed, make demo-rsync, make demo-pgbackrest, make benchmark, make report).

• Appendix B: Schema DDL definitions (sql/schema.sql) and initial seed data (sql/seed.sql).

• Appendix C: Test suite verification (8 pytest tests passing with 100% coverage on core constraints).

• Appendix D: Raw logs and benchmark CSV traces (results/logs/, results/backup_benchmarks.csv).
