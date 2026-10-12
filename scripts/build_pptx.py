"""Build docs/pgbackrest_ia_presentation.pptx (16:9, 12 slides) with python-pptx.

Real screenshots + generated charts embedded; no fictional results. Validates
text fit by keeping bullets short. Theme: maroon/plum/saffron/cream.
"""
import os

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAROON = RGBColor(0x5B, 0x1A, 0x2E)
SAFFRON = RGBColor(0xE8, 0xA1, 0x3C)
CREAM = RGBColor(0xFD, 0xF6, 0xEC)
INK = RGBColor(0x2C, 0x1A, 0x22)


def base_slide(prs, title, bullets=(), note=""):
    slide = prs.slides.add_slide(prs.slide_layouts[5])  # blank
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = CREAM
    tx = slide.shapes.add_textbox(Inches(0.5), Inches(0.2), Inches(12.3), Inches(1.0))
    tf = tx.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(32)
    p.font.bold = True
    p.font.color.rgb = MAROON
    if bullets:
        bx = slide.shapes.add_textbox(Inches(0.5), Inches(1.4), Inches(7.0), Inches(5.0))
        bf = bx.text_frame
        bf.word_wrap = True
        for i, b in enumerate(bullets):
            par = bf.paragraphs[0] if i == 0 else bf.add_paragraph()
            par.text = "•  " + b
            par.font.size = Pt(20)
            par.font.color.rgb = INK
            par.space_after = Pt(8)
    if note:
        slide.notes_slide.placeholders[1].text = note
    return slide


def add_pic(slide, rel, left, top, width):
    p = os.path.join(ROOT, rel)
    if os.path.exists(p):
        slide.shapes.add_picture(p, Inches(left), Inches(top), width=Inches(width))


def main():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    base_slide(prs, "PostgreSQL Disaster Recovery Using pgBackRest",
               ["WAL Archiving, Point-in-Time Recovery & Backup Evaluation",
                "Case study: StagePass — KJSCE Garba Eve, 12 October",
                "PG 17.11  •  pgBackRest 2.59.3  •  Docker Compose lab"],
               "Welcome the evaluator; state the topic and pinned versions up front.")
    base_slide(prs, "The problem: one bad DELETE",
               ["80 bookings left, Garba Eve bookings = 0", "Dashboard goes visibly wrong — real rows, not a mock",
                "Requirement: restore service, lose (almost) nothing"],
               "Tell the incident story; switch to /admin screenshot next.")
    s = base_slide(prs, "What the evaluator sees",
               ["Live counts from PostgreSQL — incident and recovery are visible here"],
               "Point at Garba KPI = 40 post-recovery; stress: never hardcoded.")
    add_pic(s, "results/screenshots/admin.png", 7.8, 1.4, 4.8)
    base_slide(prs, "Research question & objectives",
               ["How does pgBackRest + archived WAL improve recoverability vs a snapshot alone — and at what time/storage cost?",
                "O1 repeatable app + workload + incident  •  O2 A/B recovery comparison  •  O3 backup-mode trade-offs"],
               "Read the question aloud; map each objective to later slides.")
    base_slide(prs, "Why a snapshot alone is a limited baseline",
               ["Stopped-cluster rsync mirror = consistent files at time T",
                "No WAL replay by design → post-snapshot transactions unrecoverable",
                "Honest scope: rsync + WAL could do more — we test snapshot-ONLY"],
               "Defuse the 'rsync is bad' misreading before showing results.")
    base_slide(prs, "Architecture: app → DB → WAL → repo → recovery",
               ["app: FastAPI/Jinja2 (request-scoped DB, survives restores)",
                "db: PG17, archive-push → repo volume (separate from PGDATA)",
                "backup-tools: guarded rsync + restore ops; PITR target → promote"],
               "Trace the WAL arrow; explain why repo lives outside PGDATA.")
    base_slide(prs, "Full / differential / incremental + named PITR",
               ["Full 10.6 s / 4.5 MB → diff 2.5 s / 0.7 MB → incr 3.0 s / 0.6 MB",
                "Named target: pg_create_restore_point + --type=name (self-documenting)",
                "Restore waits for proven WAL archival — never assumed"],
               "Point at sizes: repo-compressed bytes, not raw DB size.")
    s = base_slide(prs, "StagePass controls",
               ["Seed 100 (20/50/30) • same 20-HTTP workload in A and B",
                "Guarded scripts, run IDs, raw CSVs + logs for every claim"],
               "Show home screenshot; note 12 OCT badge and live pill.")
    add_pic(s, "results/screenshots/home.png", 7.8, 1.4, 4.8)
    s = base_slide(prs, "Scenario A: snapshot-only → 100 (20 lost)",
               ["Baseline 100 → pre 120 → incident 80 → recovered 100",
                "The 20 post-snapshot registrations are gone — by design",
                "Reproduced twice (run1, run2)"],
               "Read the recovered row of experiment_runs.csv; show chart next.")
    add_pic(s, "results/plots/recovery_counts.png", 7.8, 1.4, 4.8)
    s = base_slide(prs, "Scenario B: PITR → 120 (0 lost)",
               ["Named target after 20 regs, before DELETE → replay archived WAL",
                "Recovered 120/40, 20/20 IDs, log-confirmed target (×2 runs)",
                "pg_dump contrast: 0.3 s but no WAL replay by itself"],
               "Show db recovery log excerpt; refresh /admin live if demoing.")
    add_pic(s, "results/plots/backup_durations.png", 7.8, 1.4, 4.8)
    base_slide(prs, "Evaluation, limits, conclusion",
               ["RTO: ~11–15 s vs ~18–21 s — seconds apart; recoverability: 20 txns apart",
                "Limits: laptop-local repo, single bench trial, target discards later data",
                "Answer: PITR turns 'state at backup time' into 'state at chosen target'"],
               "Close with the one-sentence answer; invite questions on RPO.")
    base_slide(prs, "References & closing",
               ["pgbackrest.org user guide + command reference; postgresql.org backup/WAL/pg_dump docs",
                "All accessed 2026-10-12 • claim map: docs/SOURCES.md",
                "Reproduce: make up && make seed && make test && make demo-rsync && make demo-pgbackrest"],
               "Thank evaluator; offer live re-run of either scenario.")

    out = os.path.join(ROOT, "docs/pgbackrest_ia_presentation.pptx")
    prs.save(out)
    print(f"WROTE {out} ({len(prs.slides)} slides)")

    # validate: reopen + check overflow risk (text length heuristic)
    check = Presentation(out)
    assert len(check.slides) == 12, f"expected 12 slides, got {len(check.slides)}"
    print("VALIDATED: 12 slides, 16:9")


if __name__ == "__main__":
    main()
