"""Build docs/pgbackrest_ia_presentation.pptx using the official KJSSE PPT Template.

Topic: Automated PostgreSQL Backup and Point-in-Time Recovery using pgBackRest
Description: Demonstrates how pgBackRest automates PostgreSQL database backups, WAL archiving,
and disaster recovery. Explores restoring a database to a specific point in time after accidental data loss,
evaluating recovery time and reliability without requiring cloud infrastructure.

Ensures:
- Exact template inheritance from 'KJSSE  PPT Template.pptx' (official logos, headers, footers).
- Strict layout budgeting: all content bounded between y=1.85in and y=5.85in (no bottom overflow).
- Card layouts, metrics, embedded screenshots, and plots.
- Preserves slide speaker notes for all 12 slides.
"""
import os
import shutil
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_PATH = os.path.join(ROOT, "KJSSE  PPT Template.pptx")
OUTPUT_PATH = os.path.join(ROOT, "docs", "pgbackrest_ia_presentation.pptx")

# Color Palette (Corporate Academic KJSCE Theme)
MAROON = RGBColor(0x5B, 0x1A, 0x2E)
MAROON_DARK = RGBColor(0x38, 0x0C, 0x17)
SAFFRON = RGBColor(0xE8, 0xA1, 0x3C)
SLATE_DARK = RGBColor(0x1E, 0x29, 0x3B)
TEXT_BODY = RGBColor(0x33, 0x41, 0x55)
TEXT_MUTED = RGBColor(0x64, 0x74, 0x8B)
CARD_BG = RGBColor(0xFF, 0xFF, 0xFF)
CARD_BORDER = RGBColor(0xCB, 0xD5, 0xE1)
EMERALD = RGBColor(0x05, 0x96, 0x69)
EMERALD_BG = RGBColor(0xEC, 0xFD, 0xF5)
EMERALD_BORDER = RGBColor(0x6E, 0xE7, 0xB7)
RED = RGBColor(0xDC, 0x26, 0x26)
RED_BG = RGBColor(0xFE, 0xF2, 0xF2)
RED_BORDER = RGBColor(0xFC, 0xA5, 0xA5)
LIGHT_GRAY_BG = RGBColor(0xF8, 0xFA, 0xFC)


def add_card(slide, left, top, width, height, bg_color=CARD_BG, border_color=CARD_BORDER):
    """Draw a clean rounded card shape to contain text and avoid overflow."""
    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(left), Inches(top), Inches(width), Inches(height)
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = bg_color
    shape.line.color.rgb = border_color
    shape.line.width = Pt(1.2)
    return shape


def add_formatted_text(slide, left, top, width, height, paragraphs_data, margin=0.12):
    """Add a text box with word wrapping and strict margin control."""
    txBox = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = txBox.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(margin)
    tf.margin_right = Inches(margin)
    tf.margin_top = Inches(margin)
    tf.margin_bottom = Inches(margin)

    for i, p_data in enumerate(paragraphs_data):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        if isinstance(p_data, str):
            p.text = p_data
            p.font.size = Pt(11)
            p.font.color.rgb = TEXT_BODY
        elif isinstance(p_data, dict):
            p.text = p_data.get("text", "")
            p.font.size = Pt(p_data.get("size", 11))
            p.font.bold = p_data.get("bold", False)
            if "color" in p_data:
                p.font.color.rgb = p_data["color"]
            if "align" in p_data:
                p.alignment = p_data["align"]
            if "space_after" in p_data:
                p.space_after = Pt(p_data["space_after"])
        elif isinstance(p_data, list):
            for r_data in p_data:
                run = p.add_run()
                run.text = r_data.get("text", "")
                run.font.size = Pt(r_data.get("size", 11))
                run.font.bold = r_data.get("bold", False)
                if "color" in r_data:
                    run.font.color.rgb = r_data["color"]
    return txBox


def add_image_safely(slide, rel_path, left, top, width, height=None):
    p = os.path.join(ROOT, rel_path)
    if os.path.exists(p):
        kwargs = {"width": Inches(width)}
        if height:
            kwargs["height"] = Inches(height)
        return slide.shapes.add_picture(p, Inches(left), Inches(top), **kwargs)
    return None


def set_slide_note(slide, note):
    if note and slide.notes_slide:
        slide.notes_slide.placeholders[1].text = note


def build_presentation():
    prs = Presentation(TEMPLATE_PATH)
    layout_title_only = prs.slide_layouts[2]

    # Delete extra slide 2 from template, keeping Slide 1
    while len(prs.slides) > 1:
        rId = prs.slides._sldIdLst[1].rId
        prs.part.drop_rel(rId)
        del prs.slides._sldIdLst[1]

    # ==============================================================
    # SLIDE 1: OFFICIAL TEMPLATE TITLE SLIDE
    # ==============================================================
    s1 = prs.slides[0]
    for sh in s1.shapes:
        if sh.has_text_frame:
            txt = sh.text_frame.text
            if "Title" in txt:
                sh.text_frame.text = "Automated PostgreSQL Backup and Point-in-Time Recovery using pgBackRest"
                for p in sh.text_frame.paragraphs:
                    p.font.size = Pt(23)
                    p.font.bold = True
                    p.font.color.rgb = MAROON
            elif "Presenter" in txt or "Affiliation" in txt:
                sh.text_frame.text = ""
                p1 = sh.text_frame.paragraphs[0]
                p1.text = "Automating Database Backups, WAL Archiving & Disaster Recovery without Cloud Infrastructure"
                p1.font.size = Pt(12)
                p1.font.bold = True
                p1.font.color.rgb = SLATE_DARK
                p1.space_after = Pt(4)

                p2 = sh.text_frame.add_paragraph()
                p2.text = "Demonstrated via StagePass (KJSCE Garba Eve) • PostgreSQL 17.11 & pgBackRest 2.59.3"
                p2.font.size = Pt(10)
                p2.font.color.rgb = TEXT_MUTED
                p2.space_after = Pt(4)

                p3 = sh.text_frame.add_paragraph()
                p3.text = "Team: Aaryan Sharma (16010123012) • Anamay Narkar (16010123040) • Aditya Singh (16010123025) • Vraj Soni (160101220)"
                p3.font.size = Pt(9)
                p3.font.bold = True
                p3.font.color.rgb = MAROON

    set_slide_note(s1, "Welcome the evaluator; introduce team members: Aaryan Sharma (16010123012), Anamay Narkar (16010123040), Aditya Singh (16010123025), Vraj Soni (160101220). State the project topic: Automated PostgreSQL Backup and Point-in-Time Recovery using pgBackRest without cloud infrastructure.")

    # ==============================================================
    # SLIDE 2: THE PROBLEM (ONE BAD DELETE)
    # ==============================================================
    s2 = prs.slides.add_slide(layout_title_only)
    s2.shapes.title.text = "The Production Incident: Accidental DELETE"

    # Left Narrative Card
    add_card(s2, 0.92, 1.85, 6.40, 3.90)
    add_formatted_text(s2, 0.92, 1.85, 6.40, 3.90, [
        {"text": "INCIDENT SCENARIO & BUSINESS IMPACT", "size": 11, "bold": True, "color": MAROON, "space_after": 6},
        [
            {"text": "• Production Context: ", "bold": True, "size": 10.5, "color": SLATE_DARK},
            {"text": "Peak online booking window for the KJSCE Garba Eve event.\n", "size": 10.5, "color": TEXT_BODY}
        ],
        [
            {"text": "• Operator Catastrophe: ", "bold": True, "size": 10.5, "color": RED},
            {"text": "An unconstrained SQL maintenance statement is issued:\n", "size": 10.5, "color": TEXT_BODY}
        ],
        {"text": "   DELETE FROM bookings WHERE event_id = 1;\n", "size": 10, "bold": True, "color": MAROON_DARK, "space_after": 4},
        [
            {"text": "• Immediate Impact: ", "bold": True, "size": 10.5, "color": SLATE_DARK},
            {"text": "Total bookings drop from 120 to 80. All Garba bookings read exactly 0 on the live operations dashboard.\n", "size": 10.5, "color": TEXT_BODY}
        ],
        [
            {"text": "• Disaster Recovery Mandate: ", "bold": True, "size": 10.5, "color": EMERALD},
            {"text": "Restore service automatically to the pre-incident point in time while evaluating recovery time and reliability without cloud infrastructure.", "size": 10.5, "color": TEXT_BODY}
        ]
    ])

    # Right Column: Two Metric Cards
    add_card(s2, 7.55, 1.85, 4.85, 1.85, bg_color=RED_BG, border_color=RED_BORDER)
    add_formatted_text(s2, 7.55, 1.85, 4.85, 1.85, [
        {"text": "GARBA BOOKINGS AT INCIDENT", "size": 10, "bold": True, "color": RED, "space_after": 2},
        {"text": "0", "size": 38, "bold": True, "color": RED, "space_after": 2},
        {"text": "40 Confirmed Registrations Instantly Wiped", "size": 10.5, "bold": True, "color": SLATE_DARK}
    ])

    add_card(s2, 7.55, 3.90, 4.85, 1.85, bg_color=EMERALD_BG, border_color=EMERALD_BORDER)
    add_formatted_text(s2, 7.55, 3.90, 4.85, 1.85, [
        {"text": "CONTROLLED RECOVERY TARGET", "size": 10, "bold": True, "color": EMERALD, "space_after": 2},
        {"text": "20 / 20", "size": 34, "bold": True, "color": EMERALD, "space_after": 2},
        {"text": "Target: Recover All 20 Post-Backup Registrations in this Test", "size": 9.5, "bold": True, "color": SLATE_DARK}
    ])

    set_slide_note(s2, "Tell the incident story: peak registrations, accidental DELETE, dashboard drops to 80/0. State the recovery criteria.")

    # ==============================================================
    # SLIDE 3: EVALUATOR VIEW (LIVE OPERATIONS DASHBOARD)
    # ==============================================================
    s3 = prs.slides.add_slide(layout_title_only)
    s3.shapes.title.text = "Observable State: Live Operations Dashboard (/admin)"

    # Left Narrative Card
    add_card(s3, 0.92, 1.85, 5.20, 3.90)
    add_formatted_text(s3, 0.92, 1.85, 5.20, 3.90, [
        {"text": "REAL-TIME POSTGRESQL INTROSPECTION", "size": 11, "bold": True, "color": MAROON, "space_after": 6},
        [
            {"text": "• Live Query Execution: ", "bold": True, "size": 10.5, "color": SLATE_DARK},
            {"text": "The /admin endpoint queries PostgreSQL relations live on every HTTP request—nothing is mocked or hardcoded.\n", "size": 10.5, "color": TEXT_BODY}
        ],
        [
            {"text": "• Real-Time Metrics: ", "bold": True, "size": 10.5, "color": SLATE_DARK},
            {"text": "Displays Total Bookings (120), Garba Bookings (40), and Event Capacity live.\n", "size": 10.5, "color": TEXT_BODY}
        ],
        [
            {"text": "• Audit Trail Inspection: ", "bold": True, "size": 10.5, "color": SLATE_DARK},
            {"text": "Shows attendee IDs (bk_seed_... vs HTTP batch IDs) for verification.\n", "size": 10.5, "color": TEXT_BODY}
        ],
        [
            {"text": "• Immediate Incident Proof: ", "bold": True, "size": 10.5, "color": RED},
            {"text": "When the DELETE runs, refreshing this dashboard immediately reports Garba = 0.", "size": 10.5, "color": TEXT_BODY}
        ]
    ])

    # Right Screenshot Frame
    add_card(s3, 6.35, 1.85, 6.05, 3.90)
    add_image_safely(s3, "results/screenshots/admin.png", 6.45, 1.95, 5.85, 3.45)
    add_formatted_text(s3, 6.35, 5.45, 6.05, 0.30, [
        {"text": "Figure: StagePass Operations Center showing post-recovery state (120/40).", "size": 9, "color": TEXT_MUTED, "align": PP_ALIGN.CENTER}
    ])

    set_slide_note(s3, "Point at Garba KPI = 40 post-recovery. Stress that nothing is mocked; the web server queries PostgreSQL on every request.")

    # ==============================================================
    # SLIDE 4: RESEARCH QUESTION & OBJECTIVES
    # ==============================================================
    s4 = prs.slides.add_slide(layout_title_only)
    s4.shapes.title.text = "Project Objectives & Evaluation Scope"

    # Top RQ Banner Card
    add_card(s4, 0.92, 1.85, 11.50, 1.15, bg_color=LIGHT_GRAY_BG, border_color=SAFFRON)
    add_formatted_text(s4, 0.92, 1.85, 11.50, 1.15, [
        {"text": "PROJECT FOCUS & CORE RESEARCH QUESTION", "size": 10, "bold": True, "color": MAROON, "space_after": 2},
        {"text": "“This project demonstrates how pgBackRest automates PostgreSQL database backups, WAL archiving, and disaster recovery. It explores restoring a database to a specific point in time after accidental data loss, evaluating recovery time and reliability without requiring cloud infrastructure.”", "size": 10.5, "bold": True, "color": SLATE_DARK}
    ])

    # Three Objective Cards
    objs = [
        {"id": "O1", "title": "Automated Lab Platform", "desc": "Build StagePass app, schema constraints, deterministic 100-row seed and realistic HTTP workload runner.", "target": "Slide 6 & 8"},
        {"id": "O2", "title": "Zero-Cloud Disaster Recovery", "desc": "Evaluate Point-in-Time Recovery to a target point after data loss vs stopped filesystem snapshots.", "target": "Slide 9 & 10"},
        {"id": "O3", "title": "Recovery Time & Reliability", "desc": "Quantify Full vs Diff vs Incr backup duration, compressed footprint, and pg_dump baseline on 20k rows.", "target": "Slide 7 & 11"}
    ]
    for i, o in enumerate(objs):
        x = 0.92 + i * 3.90
        add_card(s4, x, 3.15, 3.70, 2.60)
        add_formatted_text(s4, x, 3.15, 3.70, 2.60, [
            {"text": f"[{o['id']}] {o['title']}", "size": 11.5, "bold": True, "color": MAROON, "space_after": 4},
            {"text": o["desc"] + "\n", "size": 10, "color": TEXT_BODY, "space_after": 4},
            {"text": f"Mapped: {o['target']}", "size": 9.5, "bold": True, "color": SAFFRON}
        ])

    set_slide_note(s4, "State the project objectives: automated backup, continuous WAL archiving, disaster recovery without cloud infrastructure.")

    # ==============================================================
    # SLIDE 5: WHY SNAPSHOT-ONLY IS LIMITED
    # ==============================================================
    s5 = prs.slides.add_slide(layout_title_only)
    s5.shapes.title.text = "Theoretical Foundation: Physical Snapshot vs WAL Replay"

    # Left Column: Stopped Rsync
    add_card(s5, 0.92, 1.85, 5.60, 3.90)
    add_formatted_text(s5, 0.92, 1.85, 5.60, 3.90, [
        {"text": "BASELINE: STOPPED RSYNC SNAPSHOT", "size": 11, "bold": True, "color": RED, "space_after": 6},
        [
            {"text": "• Consistent File State at Time T:\n", "bold": True, "size": 10.5, "color": SLATE_DARK},
            {"text": "PostgreSQL is stopped cleanly; PGDATA is mirrored with rsync -aHAX --delete. Guarantees consistency at snapshot time.\n\n", "size": 10, "color": TEXT_BODY}
        ],
        [
            {"text": "• Zero Post-Snapshot Visibility:\n", "bold": True, "size": 10.5, "color": RED},
            {"text": "Without archived write-ahead logs, any transaction written at T + 1 is permanently unrecoverable.\n\n", "size": 10, "color": TEXT_BODY}
        ],
        [
            {"text": "• Realistic Industry Scope:\n", "bold": True, "size": 10.5, "color": SLATE_DARK},
            {"text": "Rsync with manual WAL archiving could do more, but enterprise teams frequently rely on storage snapshots alone.", "size": 10, "color": TEXT_BODY}
        ]
    ])

    # Right Column: pgBackRest PITR
    add_card(s5, 6.82, 1.85, 5.60, 3.90, bg_color=EMERALD_BG, border_color=EMERALD_BORDER)
    add_formatted_text(s5, 6.82, 1.85, 5.60, 3.90, [
        {"text": "CHAMPION: PGBACKREST + CONTINUOUS WAL", "size": 11, "bold": True, "color": EMERALD, "space_after": 6},
        [
            {"text": "• Automated Continuous Archiving:\n", "bold": True, "size": 10.5, "color": SLATE_DARK},
            {"text": "PostgreSQL archive_command pushes every 16 MB WAL segment and archive_timeout threshold outside PGDATA automatically.\n\n", "size": 10, "color": TEXT_BODY}
        ],
        [
            {"text": "• WAL Replay Precision:\n", "bold": True, "size": 10.5, "color": EMERALD},
            {"text": "Restores base physical backup, then replays WAL records up to a specific transaction, LSN, or named restore point.\n\n", "size": 10, "color": TEXT_BODY}
        ],
        [
            {"text": "• Granular Disaster Recovery:\n", "bold": True, "size": 10.5, "color": SLATE_DARK},
            {"text": "Shifts recovery from 'restore to backup time' to 'recovery to a named restore point recorded in WAL'.", "size": 10, "color": TEXT_BODY}
        ]
    ])

    set_slide_note(s5, "Defuse the 'rsync is bad' misreading: stopped rsync is perfectly consistent at time T. But snapshot-only cannot replay post-snapshot transactions.")

    # ==============================================================
    # SLIDE 6: ARCHITECTURE
    # ==============================================================
    s6 = prs.slides.add_slide(layout_title_only)
    s6.shapes.title.text = "System Architecture: Automated Local DR Stack"

    # 4 Architecture Nodes
    nodes = [
        {"title": "StagePass App", "sub": "FastAPI (:8000)", "desc": "Request-scoped pool\nSurvives DB downtime", "color": MAROON},
        {"title": "PostgreSQL 17.11", "sub": "Host :5433 | Container :5432", "desc": "wal_level=replica\narchive_mode=on", "color": SLATE_DARK},
        {"title": "Dedicated Repo", "sub": "Volume (/var/lib/pgbackrest)", "desc": "Isolated from PGDATA\nFull/Diff/Incr + WAL", "color": MAROON},
        {"title": "Backup-Tools", "sub": "Operational Sidecar", "desc": "Guarded restore CLI\nLSN verification gates", "color": EMERALD}
    ]
    for i, n in enumerate(nodes):
        x = 0.92 + i * 2.92
        add_card(s6, x, 1.85, 2.74, 2.20)
        add_formatted_text(s6, x, 1.85, 2.74, 2.20, [
            {"text": n["title"], "size": 11.5, "bold": True, "color": n["color"], "align": PP_ALIGN.CENTER},
            {"text": n["sub"], "size": 9.5, "bold": True, "color": SAFFRON, "align": PP_ALIGN.CENTER, "space_after": 4},
            {"text": n["desc"], "size": 10, "color": TEXT_BODY, "align": PP_ALIGN.CENTER}
        ])

    # Bottom Safety Box
    add_card(s6, 0.92, 4.20, 11.50, 1.55, bg_color=LIGHT_GRAY_BG)
    add_formatted_text(s6, 0.92, 4.20, 11.50, 1.55, [
        {"text": "RELIABILITY WITHOUT CLOUD INFRASTRUCTURE", "size": 10.5, "bold": True, "color": MAROON, "space_after": 2},
        [
            {"text": "1. Local Volume Isolation: ", "bold": True, "size": 10, "color": SLATE_DARK},
            {"text": "PGDATA and pgBackRest repository live on distinct Docker volumes; restore never overwrites backup storage.\n", "size": 10, "color": TEXT_BODY}
        ],
        [
            {"text": "2. Connection Resilience: ", "bold": True, "size": 10, "color": SLATE_DARK},
            {"text": "FastAPI uses scoped sessions; when DB restarts during restore, web requests fail gracefully and reconnect cleanly.\n", "size": 10, "color": TEXT_BODY}
        ],
        [
            {"text": "3. Automated Guard Scripts: ", "bold": True, "size": 10, "color": SLATE_DARK},
            {"text": "Strict assertions verify stanza health, LSN archival status, and container state before triggering commands.", "size": 10, "color": TEXT_BODY}
        ]
    ])

    set_slide_note(s6, "Trace the data flow: app writes to DB, WAL is pushed to repository volume /var/lib/pgbackrest, backup-tools controls PITR restore.")

    # ==============================================================
    # SLIDE 7: BACKUP MODES + NAMED PITR
    # ==============================================================
    s7 = prs.slides.add_slide(layout_title_only)
    s7.shapes.title.text = "Backup Automation & Self-Documenting Named PITR"

    modes = [
        {"name": "FULL BACKUP", "dur": "10.6 s", "size": "4.5 MB", "ratio": "Base", "desc": "Individual backup: 4.5 MB (cumulative repo: 12.1 MB). Complete physical copy + active WAL.", "color": MAROON},
        {"name": "DIFFERENTIAL", "dur": "2.5 s", "size": "697.7 KB", "ratio": "84.5% Saving", "desc": "Individual backup: 697.7 KB (cumulative repo: 14.3 MB). Copies pages modified since last Full.", "color": SAFFRON},
        {"name": "INCREMENTAL", "dur": "3.0 s", "size": "635.8 KB", "ratio": "85.9% Saving", "desc": "Individual backup: 635.8 KB (cumulative repo: 16.3 MB). Copies changes since preceding backup.", "color": EMERALD}
    ]
    for i, m in enumerate(modes):
        x = 0.92 + i * 3.90
        add_card(s7, x, 1.85, 3.70, 2.25)
        add_formatted_text(s7, x, 1.85, 3.70, 2.25, [
            {"text": m["name"], "size": 11, "bold": True, "color": m["color"], "space_after": 2},
            {"text": f"{m['dur']}  |  {m['size']}", "size": 16, "bold": True, "color": SLATE_DARK, "space_after": 2},
            {"text": f"Footprint: {m['ratio']}", "size": 10, "bold": True, "color": MAROON, "space_after": 4},
            {"text": m["desc"], "size": 9.5, "color": TEXT_BODY}
        ])

    # Bottom Named PITR Card
    add_card(s7, 0.92, 4.25, 11.50, 1.50, bg_color=LIGHT_GRAY_BG)
    add_formatted_text(s7, 0.92, 4.25, 11.50, 1.50, [
        {"text": "AUTOMATED POINT-IN-TIME RECOVERY TO TARGET POINT", "size": 10.5, "bold": True, "color": MAROON, "space_after": 2},
        [
            {"text": "• Elimination of Clock Skew: ", "bold": True, "size": 10, "color": SLATE_DARK},
            {"text": "Plants a named restore point: SELECT pg_create_restore_point('stagepass_before_incident_pgbackrest_run2');\n", "size": 10, "color": TEXT_BODY}
        ],
        [
            {"text": "• Guaranteed Archival Gate: ", "bold": True, "size": 10, "color": EMERALD},
            {"text": "Timeline-aware check verifies WAL segment reached repository disk before proceeding with restore.\n", "size": 10, "color": TEXT_BODY}
        ],
        [
            {"text": "• Precise Target Recovery: ", "bold": True, "size": 10, "color": SLATE_DARK},
            {"text": "pgbackrest restore --type=name --target=stagepass_before_incident_pgbackrest_run2 --target-action=promote replays WAL to point.", "size": 10, "color": TEXT_BODY}
        ]
    ])

    set_slide_note(s7, "Distinguish individual backup size (4.5MB/698KB/636KB) from cumulative repo size (12.1MB/14.3MB/16.3MB). Highlight named restore point and archival safety gate.")

    # ==============================================================
    # SLIDE 8: STAGEPASS CONTROLS & METHODOLOGY
    # ==============================================================
    s8 = prs.slides.add_slide(layout_title_only)
    s8.shapes.title.text = "Experimental Controls & Repeatability Rigor"

    # Left Narrative Card
    add_card(s8, 0.92, 1.85, 5.20, 3.90)
    add_formatted_text(s8, 0.92, 1.85, 5.20, 3.90, [
        {"text": "METHODOLOGICAL GUARDS & INVARIANTS", "size": 11, "bold": True, "color": MAROON, "space_after": 6},
        [
            {"text": "• Deterministic 100-Row Seed:\n", "bold": True, "size": 10.5, "color": SLATE_DARK},
            {"text": "Fixed distribution (20 Garba, 50 TechSummit, 30 MusicFest) seeded identically for both scenarios.\n\n", "size": 10, "color": TEXT_BODY}
        ],
        [
            {"text": "• Identical 20-HTTP Workload:\n", "bold": True, "size": 10.5, "color": SLATE_DARK},
            {"text": "20 real HTTP registration payloads executed via scripts/workload.py against /api/events/kjsce-garba-eve/register.\n\n", "size": 10, "color": TEXT_BODY}
        ],
        [
            {"text": "• Two-Phase Replication (Run 1 & Run 2):\n", "bold": True, "size": 10.5, "color": SLATE_DARK},
            {"text": "Every test run twice from scratch with isolated run IDs, raw CSV logs, and terminal recordings.\n\n", "size": 10, "color": TEXT_BODY}
        ],
        [
            {"text": "• Automated Test Suite:\n", "bold": True, "size": 10.5, "color": EMERALD},
            {"text": "8 pytest tests validate database constraints, transaction isolation, and health endpoints.", "size": 10, "color": TEXT_BODY}
        ]
    ])

    # Right Screenshot Frame
    add_card(s8, 6.35, 1.85, 6.05, 3.90)
    add_image_safely(s8, "results/screenshots/home.png", 6.45, 1.95, 5.85, 3.45)
    add_formatted_text(s8, 6.35, 5.45, 6.05, 0.30, [
        {"text": "Figure: StagePass Home UI: 12 OCT badge, live pill, and booking modal.", "size": 9, "color": TEXT_MUTED, "align": PP_ALIGN.CENTER}
    ])

    set_slide_note(s8, "Show home screenshot with 12 OCT badge and live pill. Mention that seed is always 100 bookings and both scenarios receive identical 20 HTTP registrations.")

    # ==============================================================
    # SLIDE 9: SCENARIO A RESULT (SNAPSHOT BASELINE)
    # ==============================================================
    s9 = prs.slides.add_slide(layout_title_only)
    s9.shapes.title.text = "Scenario A: Stopped Rsync Snapshot Alone (Data Loss)"

    # Left Column: Result Breakdown
    add_card(s9, 0.92, 1.85, 6.10, 3.90)
    add_formatted_text(s9, 0.92, 1.85, 6.10, 3.90, [
        {"text": "EXECUTION TIMELINE & DATA LOSS REASONING", "size": 11, "bold": True, "color": RED, "space_after": 6},
        [
            {"text": "1. Baseline Snapshot Taken: ", "bold": True, "size": 10, "color": SLATE_DARK},
            {"text": "Cluster stopped, rsync snapshot created at 100 bookings (20 Garba).\n", "size": 10, "color": TEXT_BODY}
        ],
        [
            {"text": "2. Live Traffic Ingestion: ", "bold": True, "size": 10, "color": SLATE_DARK},
            {"text": "20 valid attendees register via HTTP; count climbs to 120 (40 Garba).\n", "size": 10, "color": TEXT_BODY}
        ],
        [
            {"text": "3. Operator Disaster: ", "bold": True, "size": 10, "color": RED},
            {"text": "DELETE query wipes all Garba registrations; count plunges to 80.\n", "size": 10, "color": TEXT_BODY}
        ],
        [
            {"text": "4. Disaster Recovery Restored: ", "bold": True, "size": 10, "color": SLATE_DARK},
            {"text": "Cluster stopped, rsync snapshot restored, PostgreSQL restarted.\n\n", "size": 10, "color": TEXT_BODY}
        ],
        [
            {"text": "• Final Evaluated State: ", "bold": True, "size": 10.5, "color": RED},
            {"text": "100 Total / 20 Garba. Exactly ZERO of the 20 post-snapshot registrations survived (reproduced twice).", "size": 10.5, "color": TEXT_BODY}
        ]
    ])

    # Right Column: Metric Callout Cards
    add_card(s9, 7.25, 1.85, 5.15, 1.85, bg_color=RED_BG, border_color=RED_BORDER)
    add_formatted_text(s9, 7.25, 1.85, 5.15, 1.85, [
        {"text": "TRANSACTIONS PRESERVED (RPO)", "size": 10, "bold": True, "color": RED, "space_after": 2},
        {"text": "0 / 20 (0%)", "size": 36, "bold": True, "color": RED, "space_after": 2},
        {"text": "20 Legitimate Registrations Permanently Lost", "size": 10.5, "bold": True, "color": SLATE_DARK}
    ])

    add_card(s9, 7.25, 3.90, 5.15, 1.85, bg_color=LIGHT_GRAY_BG)
    add_formatted_text(s9, 7.25, 3.90, 5.15, 1.85, [
        {"text": "MEASURED TIME METRICS (RUN 1 & 2)", "size": 10, "bold": True, "color": MAROON, "space_after": 4},
        [
            {"text": "• Snapshot Duration: ", "bold": True, "size": 10, "color": SLATE_DARK},
            {"text": "0.5 s – 1.1 s (local disk mirror)\n", "size": 10, "color": TEXT_BODY}
        ],
        [
            {"text": "• Recovery Time (RTO): ", "bold": True, "size": 10, "color": SLATE_DARK},
            {"text": "Run 1 = 15.0 s  |  Run 2 = 10.6 s\n", "size": 10, "color": TEXT_BODY}
        ],
        [
            {"text": "• Architectural Scope: ", "bold": True, "size": 10, "color": RED},
            {"text": "Fast recovery, but snapshot lacks WAL replay mechanism by design.", "size": 10, "color": TEXT_BODY}
        ]
    ])

    set_slide_note(s9, "Snapshot, 20 registrations, DELETE, restore: back to 100, Garba 20, zero of the new twenty survive. Baseline snapshot contains no post-snapshot WAL replay.")

    # ==============================================================
    # SLIDE 10: SCENARIO B RESULT (PGBACKREST PITR)
    # ==============================================================
    s10 = prs.slides.add_slide(layout_title_only)
    s10.shapes.title.text = "Scenario B: pgBackRest with Archived WAL (Target Reached)"

    # Left Column: Result Breakdown
    add_card(s10, 0.92, 1.85, 6.10, 3.90, bg_color=EMERALD_BG, border_color=EMERALD_BORDER)
    add_formatted_text(s10, 0.92, 1.85, 6.10, 3.90, [
        {"text": "EXECUTION TIMELINE & RECOVERY LOGIC", "size": 11, "bold": True, "color": EMERALD, "space_after": 6},
        [
            {"text": "1. Online Base Backup: ", "bold": True, "size": 10, "color": SLATE_DARK},
            {"text": "pgBackRest creates hot physical backup at 100 bookings.\n", "size": 10, "color": TEXT_BODY}
        ],
        [
            {"text": "2. Live Traffic & Named Restore Point: ", "bold": True, "size": 10, "color": SLATE_DARK},
            {"text": "20 attendees register (120 total / 40 Garba). Restore point stagepass_before_incident_pgbackrest_run2 planted.\n", "size": 10, "color": TEXT_BODY}
        ],
        [
            {"text": "3. Verified Archival Guard: ", "bold": True, "size": 10, "color": EMERALD},
            {"text": "Timeline-aware check verifies WAL segment reached repository disk.\n", "size": 10, "color": TEXT_BODY}
        ],
        [
            {"text": "4. Disaster & Target PITR Restore: ", "bold": True, "size": 10, "color": SLATE_DARK},
            {"text": "DELETE wipes Garba. pgBackRest restores base backup, rolls forward WAL to target, and promotes.\n\n", "size": 10, "color": TEXT_BODY}
        ],
        [
            {"text": "• Final Evaluated State: ", "bold": True, "size": 10.5, "color": EMERALD},
            {"text": "120 Total / 40 Garba. All 20/20 tested post-backup registrations recovered!", "size": 10.5, "color": TEXT_BODY}
        ]
    ])

    # Right Column: Metric Callout Cards
    add_card(s10, 7.25, 1.85, 5.15, 1.85, bg_color=CARD_BG, border_color=EMERALD_BORDER)
    add_formatted_text(s10, 7.25, 1.85, 5.15, 1.85, [
        {"text": "TRANSACTIONS PRESERVED (TEST)", "size": 10, "bold": True, "color": EMERALD, "space_after": 2},
        {"text": "20 / 20 (100%)", "size": 36, "bold": True, "color": EMERALD, "space_after": 2},
        {"text": "Zero Loss of Tested Registrations at Target", "size": 10.5, "bold": True, "color": SLATE_DARK}
    ])

    add_card(s10, 7.25, 3.90, 5.15, 1.85, bg_color=LIGHT_GRAY_BG)
    add_formatted_text(s10, 7.25, 3.90, 5.15, 1.85, [
        {"text": "PERFORMANCE & AUDIT VALIDATION", "size": 10, "bold": True, "color": MAROON, "space_after": 4},
        [
            {"text": "• Recovery Time (RTO): ", "bold": True, "size": 10, "color": SLATE_DARK},
            {"text": "Run 1 = 17.6 s (+2.6 s delta) | Run 2 = 20.6 s (+10.0 s delta)\n", "size": 10, "color": TEXT_BODY}
        ],
        [
            {"text": "• Engine Log Proof: ", "bold": True, "size": 10, "color": MAROON},
            {"text": "'recovery stopping at restore point \"stagepass_before_incident_pgbackrest_run2\"'\n", "size": 8.2, "bold": True, "color": MAROON_DARK}
        ],
        [
            {"text": "• Production Caveat: ", "bold": True, "size": 10, "color": SLATE_DARK},
            {"text": "Experiment achieved zero loss; production RPO depends on WAL lag.", "size": 9.5, "color": TEXT_BODY}
        ]
    ])

    set_slide_note(s10, "Full backup, 20 registrations, named restore point, verified archival, DELETE, restore to name, promote. Engine logs confirm target. All 20 IDs back.")

    # ==============================================================
    # SLIDE 11: EVALUATION & BENCHMARKS
    # ==============================================================
    s11 = prs.slides.add_slide(layout_title_only)
    s11.shapes.title.text = "Quantitative Evaluation: Recovery Time & Reliability"

    # Embed Plots side-by-side
    add_card(s11, 0.92, 1.85, 5.60, 2.45)
    add_image_safely(s11, "results/plots/recovery_counts.png", 1.02, 1.95, 5.40, 2.25)

    add_card(s11, 6.82, 1.85, 5.60, 2.45)
    add_image_safely(s11, "results/plots/backup_durations.png", 6.92, 1.95, 5.40, 2.25)

    # Bottom Summary Table / Card
    add_card(s11, 0.92, 4.45, 11.50, 1.30, bg_color=LIGHT_GRAY_BG)
    add_formatted_text(s11, 0.92, 4.45, 11.50, 1.30, [
        {"text": "EMPIRICAL RECOVERY TIME & STORAGE METRICS (MEASURED DATA)", "size": 10, "bold": True, "color": MAROON, "space_after": 2},
        [
            {"text": "• Recovery Time Objective (RTO): ", "bold": True, "size": 9.5, "color": SLATE_DARK},
            {"text": "Snapshot restores in 10.6 s & 15.0 s vs pgBackRest in 17.6 s & 20.6 s (observed differences: +2.6 s in Run 1 and +10.0 s in Run 2 for full WAL replay).\n", "size": 9.5, "color": TEXT_BODY}
        ],
        [
            {"text": "• Storage & Backup Modes (Single Trial): ", "bold": True, "size": 9.5, "color": SLATE_DARK},
            {"text": "Individual backup size: Full = 4.5 MB, Diff = 697.7 KB, Incr = 635.8 KB (vs cumulative repo size: 12.1 MB, 14.3 MB, 16.3 MB). Diff/Incr save >84% backup footprint.", "size": 9.5, "color": TEXT_BODY}
        ]
    ])

    set_slide_note(s11, "RTO differs by seconds: observed run deltas of 2.6s and 10.0s. Storage chart distinguishes individual backup size from cumulative repository size.")

    # ==============================================================
    # SLIDE 12: CONCLUSION, VALIDITY & REFERENCES
    # ==============================================================
    s12 = prs.slides.add_slide(layout_title_only)
    s12.shapes.title.text = "Conclusion: Automated DR without Cloud Infrastructure"

    # Left Column: Findings
    add_card(s12, 0.92, 1.85, 5.60, 3.90)
    add_formatted_text(s12, 0.92, 1.85, 5.60, 3.90, [
        {"text": "CORE PROJECT FINDINGS", "size": 11, "bold": True, "color": MAROON, "space_after": 6},
        [
            {"text": "1. Controlled Experiment Success:\n", "bold": True, "size": 10, "color": SLATE_DARK},
            {"text": "In both recorded PITR trials, all 20 post-backup registrations were recovered by restoring to the verified pre-incident named restore point.\n\n", "size": 9.5, "color": TEXT_BODY}
        ],
        [
            {"text": "2. Production RPO Qualification:\n", "bold": True, "size": 10, "color": SLATE_DARK},
            {"text": "This experiment achieved zero loss of the 20 tested registrations; production RPO depends on WAL archival and retention.\n\n", "size": 9.5, "color": TEXT_BODY}
        ],
        [
            {"text": "3. RTO & Storage Trade-offs:\n", "bold": True, "size": 10, "color": MAROON},
            {"text": "Observed PITR recovery times of 17.6s & 20.6s (+2.6s & +10.0s over snapshot). Single-trial backup modes cut routine footprint by >84%.", "size": 9.5, "color": TEXT_BODY}
        ]
    ])

    # Right Column: References
    add_card(s12, 6.82, 1.85, 5.60, 3.90, bg_color=LIGHT_GRAY_BG)
    add_formatted_text(s12, 6.82, 1.85, 5.60, 3.90, [
        {"text": "PRIMARY REFERENCES & REPRODUCIBILITY", "size": 11, "bold": True, "color": MAROON, "space_after": 6},
        [
            {"text": "[1] pgBackRest User Guide & Architecture (v2.59.3)\n", "bold": True, "size": 9.5, "color": SLATE_DARK},
            {"text": "https://pgbackrest.org/user-guide.html\n\n", "size": 8.5, "color": TEXT_MUTED}
        ],
        [
            {"text": "[2] PostgreSQL 17 Backup and Restore Documentation\n", "bold": True, "size": 9.5, "color": SLATE_DARK},
            {"text": "https://www.postgresql.org/docs/17/backup.html\n\n", "size": 8.5, "color": TEXT_MUTED}
        ],
        [
            {"text": "[3] Continuous Archiving and PITR (Chapter 25)\n", "bold": True, "size": 9.5, "color": SLATE_DARK},
            {"text": "https://www.postgresql.org/docs/17/continuous-archiving.html\n\n", "size": 8.5, "color": TEXT_MUTED}
        ],
        [
            {"text": "• Reproducibility: ", "bold": True, "size": 10, "color": MAROON},
            {"text": "All scripts, Makefile targets, and raw CSV runs available in repository.", "size": 9.5, "color": TEXT_BODY}
        ]
    ])

    set_slide_note(s12, "Summarize the core answer to the RQ. Point to pgbackrest.org and postgresql.org references. Offer to run either scenario live via Makefile.")

    prs.save(OUTPUT_PATH)
    print(f"SUCCESS: Generated presentation for '{OUTPUT_PATH}' using KJSSE PPT Template.")


if __name__ == "__main__":
    build_presentation()
