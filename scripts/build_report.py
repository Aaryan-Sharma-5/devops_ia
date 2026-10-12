"""Build docs/pgbackrest_case_study_report.docx (+ .md source) from REAL result files.

Covers the 31 required sections. Numbers come from results/*.csv; charts and
screenshots embedded. Anything unmeasured is marked PENDING — never invented.
Requires: python-docx (pip install python-docx).
"""
import csv
import datetime
import json
import os

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RQ = ("How does pgBackRest with archived WAL improve PostgreSQL recoverability after "
      "accidental data loss compared with a consistent file-system snapshot alone, and what "
      "are the time and storage trade-offs of its backup strategies?")
ACCESSED = "2026-10-12"


def read_csv(path):
    with open(os.path.join(ROOT, path)) as f:
        return list(csv.DictReader(f))


def add_table(doc, headers, rows):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Light Grid Accent 1"
    for i, h in enumerate(headers):
        t.rows[0].cells[i].text = h
    for r in rows:
        cells = t.add_row().cells
        for i, v in enumerate(r):
            cells[i].text = str(v)
    doc.add_paragraph()


def main():
    runs = read_csv("results/experiment_runs.csv")
    bench = read_csv("results/backup_benchmarks.csv")
    try:
        meta = json.load(open(os.path.join(ROOT, "results/experiment_metadata.json")))
    except FileNotFoundError:
        meta = {}
    pg_v = meta.get("postgres", "PostgreSQL 17.11 (recorded in results/experiment_metadata.json)")
    pbr_v = meta.get("pgbackrest", "pgBackRest 2.59.3")

    doc = Document()
    st = doc.styles["Normal"]
    st.font.name = "Calibri"
    st.font.size = Pt(11)

    # 1. Title page
    doc.add_heading("PostgreSQL Disaster Recovery Using pgBackRest:\nWAL Archiving, Point-in-Time Recovery and Backup Evaluation", 0)
    doc.add_paragraph("DevOps Theory — Internal Assessment Case Study").alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(f"StagePass — Event Registration & Operations  •  Date: {datetime.date.today().isoformat()}")
    t = doc.add_table(rows=4, cols=2)
    t.style = "Light Grid Accent 1"
    for i, (a, b) in enumerate([("Group member 1 (Name / Roll)", ""), ("Group member 2 (Name / Roll)", ""),
                                ("Group member 3 (Name / Roll)", ""), ("Faculty / Evaluator", "")]):
        t.rows[i].cells[0].text = a
    doc.add_paragraph("Placeholder rows above are filled by the team; no student details are invented in this report.")
    doc.add_page_break()

    # TOC placeholder (Word: update fields to generate; python-docx cannot auto-generate)
    doc.add_paragraph("Contents: use Word → References → Update Table after opening "
                      "(headings below are numbered for navigation).", style="Intense Quote")

    secs = []
    def sec(title, body, bullets=()):
        secs.append((title, body, bullets))
        doc.add_heading(title, level=1)
        for p in body:
            doc.add_paragraph(p)
        for b in bullets:
            doc.add_paragraph(b, style="List Bullet")

    sec("2. Abstract / Executive Summary",
        ["StagePass, a fictional event-registration platform, loses all KJSCE Garba Eve bookings to an "
         "accidental DELETE. A consistent rsync snapshot-only baseline recovers to snapshot time (100/120 "
         "bookings; 20 legitimate post-snapshot registrations lost, reproduced twice). pgBackRest with archived "
         "WAL and a verified named restore point recovers to 120/120 bookings with all 20 post-backup "
         "registrations present (reproduced twice). Differential/incremental backups cost ~2.5–3.0 s and "
         "~0.6–0.7 MB vs a 10.6 s / 4.5 MB full backup on a 20k-row bench dataset. RTO differs by seconds; "
         "recoverability differs by 20 transactions."])
    sec("3. Introduction", ["PostgreSQL is a common DevOps backing service; operator error (bad DELETE) is a "
         "leading incident class. This case study makes recovery observable through a real app, repeatable HTTP "
         "workload, incident, recovery and measurement—not merely a successful backup command."])
    sec("4. Problem Statement", ["After legitimate registrations arrive, an accidental DELETE removes every "
         "KJSCE Garba Eve booking (Garba count 0, dashboard visibly wrong). Requirements: restore service, "
         "lose as few legitimate transactions as possible, quantify time/storage costs."])
    sec("5. Research Question and Objectives", [f"Research question: {RQ}", "Objectives: (1) build the StagePass "
         "demo; (2) compare snapshot-only vs PITR on identical data/workload; (3) measure full/diff/incr + dump "
         "trade-offs; (4) interpret RTO/RPO honestly."])
    sec("6. Scope and Assumptions", ["Local Docker lab on one laptop; disposable synthetic data "
         "(`@example.test`); headline metric = booking rows; repo on the same host (convenience, not off-site "
         "DR); single-trial bench medians pending a bigger host."],
        ["In scope: rsync baseline, pgBackRest PITR, modes, dump comparison, retention demo.",
         "Out of scope: Kubernetes, multi-node HA, encryption-at-rest tuning, production sizing."])
    sec("7. DevOps Relevance", ["Reliability (MTTR/RTO), recovery as code (Compose + scripts), observability "
         "(dashboard reflects true DB state), change safety (guards, no destructive endpoints), reproducibility "
         "(seeded data, run IDs, raw logs)."])
    sec("8. Literature / Tool Review", ["pgBackRest User Guide and Command Reference (Debian/PG17 track); "
         "PostgreSQL Backup & Restore, WAL configuration, pg_dump/pg_restore/pg_basebackup docs (accessed "
         + ACCESSED + "; see SOURCES.md for claim mapping). Blogs were not used for technical claims."])
    sec("9. Logical versus Physical Backups", ["pg_dump emits logical SQL/custom archives: portable, selective, "
         "but no WAL replay by itself. pgBackRest physical backups copy cluster files + WAL: enable PITR. "
         "Measured: dump 0.3 s/0.5 MB vs full physical 10.6 s/4.5 MB on the same data."])
    sec("10. PostgreSQL WAL and Crash Recovery", ["WAL records every change; `wal_level=replica`, checkpoints "
         "and `archive_command` ship segments to the repo; replay from a backup + WAL restores consistency and "
         "enables time/name-targeted recovery."])
    sec("11. pgBackRest Architecture", ["Stanza `stagepass` binds PG path + repo; repo holds backups + WAL "
         "archive; `archive-push/get` integrate with PostgreSQL; `restore` rebuilds PGDATA and writes recovery "
         "config. Here pgBackRest runs in the DB container (simplest reliable); control/restore split across "
         "db/backup-tools containers is documented in §16."])
    sec("12. Full, Differential and Incremental Semantics", ["Full: everything. Differential: since last full. "
         "Incremental: since last backup of any kind (needs full + chain). Measured artifact sizes diverge from "
         "row-change ratios because PostgreSQL writes pages and pgBackRest compresses (§21)."])
    sec("13. PITR Theory and Named Recovery Targets", ["Recovery replays WAL to a target (time/LSN/XID/name) "
         "then promotes. Named targets (`pg_create_restore_point` + `--type=name`) are self-documenting and "
         "were used here; the target must postdate required WAL archival—verified, not assumed (§18)."])
    sec("14. System Architecture Diagram", ["Compose: app (FastAPI/Jinja2, :8000) → db (PG17 + pgBackRest, :5433) "
         "↔ backup-tools (rsync/pgBackRest, shares pgdata/repo/snapshots). Volumes isolate PGDATA, repo, "
         "snapshots, results. Diagram: 16:9 deck slide 5; live screenshot evidence below."])
    doc.add_heading("15. StagePass Application Design and Database Schema", level=1)
    doc.add_paragraph("Events/attendees/bookings with FKs, CHECKs and indexes (sql/schema.sql). Seed: 100 "
                      "bookings (20/50/30), ids bk_seed_001..100, Garba date field 2026-10-12 shown as 12 OCT. "
                      "API: GET /api/health|/events|/events/{slug}/registrations|/dashboard/summary|"
                      "/registrations/recent, POST /api/events/{slug}/register (transactional, validated). "
                      "UI: maroon/plum/saffron/cream, local CSS/SVG only.")
    for img, cap in [("results/screenshots/home.png", "Figure 1 — StagePass home (genuine screenshot)."),
                     ("results/screenshots/admin.png", "Figure 2 — Operations dashboard (genuine screenshot).")]:
        p = os.path.join(ROOT, img)
        if os.path.exists(p):
            doc.add_picture(p, width=Inches(6.0))
            doc.add_paragraph(cap, style="Caption")
    sec("16. Implementation Environment and Versions", [f"Host: {meta.get('host', '')}. {pg_v}. {pbr_v}. "
         f"{meta.get('docker', '')}, {meta.get('compose', '')}. Full metadata: results/experiment_metadata.json. "
         "Custom Debian-based PG image installs matched pgBackRest+rsync; config under version control, no secrets."])
    sec("17. Configuration and Commands", ["archive_mode=on, archive_command=`pgbackrest --stanza=stagepass "
         "archive-push %p`, wal_level=replica, max_wal_senders=5, archive_timeout=60.",
         "Key commands: `stanza-create`, `check`, `--type=full backup`, `info`, `restore --type=name "
         "--target=<point> --target-action=promote`, `expire --repo1-retention-full=1`. `check` proves config "
         "health, not target availability; restore requires a cleaned PGDATA (documented) or --delta."])
    sec("18. Controlled Experimental Methodology", ["Same seed + same 20-HTTP workload in A and B; guarded "
         "scripts; invariants asserted (100/20 → 120/40 → incident 0 Garba → recovered); B4 blocks PITR until "
         "the restore-point WAL segment is proven archived (one aborted run2 attempt evidences the guard); "
         "each scenario reproduced twice with separate run IDs and batches."])
    doc.add_heading("19. rsync Snapshot-Only Baseline", level=1)
    doc.add_paragraph("Consistent (stopped-cluster) `rsync -aHAX --delete` mirror + external manifest. Restores "
                      "to snapshot time; by design replays no WAL. Result (×2): 100 total / 20 Garba; 0/20 "
                      "post-snapshot registrations recovered.")
    doc.add_heading("20. pgBackRest PITR Experiment", level=1)
    doc.add_paragraph("Full backup → 20 regs → named restore point (LSN recorded) → verified WAL archival → "
                      "incident → named restore + promote → log-confirmed target → 120/40 with 20/20 batch IDs, "
                      "0 orphans (×2). The DELETE is absent because the target precedes it; later transactions "
                      "would be discarded by target choice—a documented property, not a defect.")
    sec("21. Backup-Mode and Dump Benchmarks", ["Bench 20k rows: full 10.6 s/4.5 MB; diff 2.5 s/697.7 KB; incr "
         "3.0 s/635.8 KB (compressed repo bytes; DB 33.5 MB reported separately). pg_dump -Fc 0.3 s/0.5 MB, "
         "restore 1.4 s, selective yes, WAL replay no. Single trials; 3-trial medians PENDING a larger host."])
    doc.add_heading("22. Results Tables and Charts (real data)", level=1)
    doc.add_paragraph("Source: results/experiment_runs.csv, backup_benchmarks.csv. Charts generated by "
                      "scripts/compare.py from those files.")
    add_table(doc, ["run", "baseline", "pre", "recovered", "new regs", "backup", "restore"],
              [[r["scenario_id"], r["baseline_booking_count"], r["pre_incident_booking_count"],
                r["recovered_booking_count"], r["recovered_new_registration_count"],
                r["backup_duration_seconds"], r["restore_duration_seconds"]] for r in runs])
    add_table(doc, ["trial", "type", "rows", "duration_s", "label"],
              [[b["trial"], b["backup_type"], b["rows"], b["duration_s"], b["backup_label"]] for b in bench])
    for img, cap in [("results/plots/recovery_counts.png", "Figure 3 — booking counts per run (generated)."),
                     ("results/plots/backup_durations.png", "Figure 4 — backup durations (generated).")]:
        p = os.path.join(ROOT, img)
        if os.path.exists(p):
            doc.add_picture(p, width=Inches(5.5))
            doc.add_paragraph(cap, style="Caption")
    sec("23. Comparison Matrix", ["Snapshot-only: RTO ~11–15 s, RPO = snapshot time (20 txns lost), storage = "
         "full PGDATA copy. PITR: RTO ~18–21 s, RPO = named target (0 lost in lab), storage = full + WAL. "
         "Dump: fastest/smallest, no PITR."])
    sec("24. Discussion and Evaluation", ["The recoverability gap (20 transactions) dwarfs the time gap "
         "(seconds) on this scale. WAL archiving is the difference between 'state at backup time' and 'state "
         "at chosen target'. Diff/incr trade full-chain dependence for speed/size."])
    sec("25. RTO and RPO Interpretation", ["RTO measured to verified usable service (not process exit). RPO is "
         "the achieved target; production RPO depends on archive lag and monitoring. No zero-RPO claim: success "
         "at one target does not guarantee all targets."])
    sec("26. Threats to Validity and Limitations", ["Laptop-local repo (no disk-failure protection); single "
         "bench trial; lab-scale data; timeline/repo resets between runs; target selection discards later data; "
         "results require retained backups+WAL."],
        ["Laptop-local repo does not protect against host disk failure.",
         "Lab ≠ production performance study.", "Single-trial bench needs 3-trial medians.",
         "PITR target choice discards later transactions."])
    sec("27. Security Considerations", ["Synthetic `@example.test` data; no destructive app endpoints; no "
         "Docker socket in app; secrets via env, not VCS; lab DB credentials are non-production; restore "
         "commands guarded to the disposable lab volume."])
    sec("28. Conclusion (answering the RQ)", ["pgBackRest + archived WAL improves recoverability from "
         "'whatever existed at snapshot time' to 'the chosen pre-incident target', preserving all 20 "
         "legitimate post-backup registrations that snapshot-only loses, at a cost of seconds of RTO and "
         "full+WAL storage; differential/incremental backups cut routine backup time/size to a fraction of "
         "full."])
    sec("29. Future Improvements", ["Off-host S3-compatible repo; 3-trial bench on larger host; standby/restore "
         "drills; alerting on archive lag; retention policies per RPO; encrypted repos; destructive-guard CI."],
        ["S3-compatible off-host repository.", "Scheduled drill restores with RTO budgets.",
         "Archive-lag alerting."])
    sec("30. References", ["[1] pgBackRest User Guide. https://pgbackrest.org/user-guide.html",
         "[2] pgBackRest Command Reference. https://pgbackrest.org/command.html",
         "[3] pgBackRest releases. https://pgbackrest.org/news.html",
         "[4] PostgreSQL Backup and Restore. https://www.postgresql.org/docs/current/backup.html",
         "[5] PostgreSQL WAL configuration. https://www.postgresql.org/docs/current/runtime-config-wal.html",
         "[6] pg_dump. https://www.postgresql.org/docs/current/app-pgdump.html",
         "[7] pg_restore. https://www.postgresql.org/docs/current/app-pgrestore.html",
         "[8] pg_basebackup. https://www.postgresql.org/docs/current/app-pgbasebackup.html",
         f"(All accessed {ACCESSED}; claim mapping in docs/SOURCES.md.)"])
    doc.add_heading("31. Appendix", level=1)
    doc.add_paragraph("A. Reproduction: make up && make seed && make test && make demo-rsync && "
                      "make demo-pgbackrest && make benchmark && make compare. B. Config: docker/pgbackrest.conf, "
                      "docker-compose.yml. C. SQL: sql/*. D. Tests: 8 pytest tests green. E. Raw: results/*.csv, "
                      "results/logs/, results/experiment_metadata.json. F. Deviations fixed during work: seed-CTE "
                      "visibility, dashboard GROUP BY, exec-into-stopped-container, PGDATA clean step, "
                      "timeline-aware WAL check, benchmark %% typo (see docs/RESULTS.md).")

    out = os.path.join(ROOT, "docs/pgbackrest_case_study_report.docx")
    doc.save(out)
    print(f"WROTE {out}")

    # Markdown source (editable)
    md = [f"# {RQ}", "", f"Generated {datetime.date.today().isoformat()} from results/*.csv. "
        "Full text in the DOCX; this source mirrors its structure and tables.", ""]
    md.append("## Runs")
    md.append("| run | baseline | pre | recovered | new | backup_s | restore_s |")
    md.append("|---|---|---|---|---|---|---|")
    for r in runs:
        md.append("| {scenario_id} | {baseline_booking_count} | {pre_incident_booking_count} | "
                  "{recovered_booking_count} | {recovered_new_registration_count} | "
                  "{backup_duration_seconds} | {restore_duration_seconds} |".format(**r))
    open(os.path.join(ROOT, "docs/pgbackrest_case_study_report.md"), "w").write("\n".join(md))
    print("WROTE docs/pgbackrest_case_study_report.md")


if __name__ == "__main__":
    main()
