const PptxGenJS = require('pptxgenjs');
const path = require('path');
const fs = require('fs');

const ROOT = path.resolve(__dirname, '..');
const OUTPUT_PATH = path.join(ROOT, 'docs', 'pgbackrest_ia_presentation.pptx');

// Visual Design Tokens
const COLORS = {
  MAROON_DARK: '380C17',
  MAROON: '5B1A2E',
  MAROON_LIGHT: '832A44',
  SAFFRON: 'E8A13C',
  SAFFRON_LIGHT: 'FEF3C7',
  GOLD: 'F59E0B',
  CREAM: 'FDFBF7',
  SURFACE_LIGHT: 'F8FAFC',
  SURFACE_CARD: 'FFFFFF',
  BORDER_CARD: 'E2E8F0',
  TEXT_DARK: '0F172A',
  TEXT_BODY: '334155',
  TEXT_MUTED: '64748B',
  TEXT_LIGHT: 'F8FAFC',
  EMERALD: '059669',
  EMERALD_BG: 'ECFDF5',
  RED: 'DC2626',
  RED_BG: 'FEF2F2',
  SLATE_BG: '1E293B',
  SLATE_CARD: '334155'
};

function addHeader(slide, title, category = "DEVOPS IA CASE STUDY", isDark = false) {
  // Top category badge
  slide.addText(category.toUpperCase(), {
    x: 0.8,
    y: 0.45,
    w: 10.0,
    h: 0.3,
    fontSize: 10,
    fontFace: 'Arial',
    bold: true,
    color: isDark ? COLORS.SAFFRON : COLORS.MAROON,
    charSpacing: 2
  });

  // Main Slide Title
  slide.addText(title, {
    x: 0.8,
    y: 0.75,
    w: 11.5,
    h: 0.6,
    fontSize: 24,
    fontFace: 'Arial',
    bold: true,
    color: isDark ? COLORS.TEXT_LIGHT : COLORS.MAROON_DARK
  });

  // Subtle separator line
  slide.addShape('rect', {
    x: 0.8,
    y: 1.4,
    w: 11.7,
    h: 0.02,
    fill: { color: isDark ? '475569' : 'E2E8F0' },
    line: { color: isDark ? '475569' : 'E2E8F0' }
  });
}

function addCard(slide, x, y, w, h, bgColor = COLORS.SURFACE_CARD, borderColor = COLORS.BORDER_CARD) {
  slide.addShape('roundRect', {
    x: x,
    y: y,
    w: w,
    h: h,
    rectRadius: 0.1,
    fill: { color: bgColor },
    line: { color: borderColor, width: 1.2 }
  });
}

async function buildPresentation() {
  const pptx = new PptxGenJS();
  pptx.layout = 'LAYOUT_16x9'; // 13.33 x 7.5 inches
  pptx.author = 'KJSCE DevOps Team';
  pptx.company = 'KJSCE BTech DevOps';
  pptx.title = 'PostgreSQL Disaster Recovery Using pgBackRest';

  // ==========================================
  // SLIDE 1: TITLE SLIDE (Premium Dark Maroon)
  // ==========================================
  {
    const slide = pptx.addSlide();
    slide.background = { color: COLORS.MAROON_DARK };

    // Decorative background element
    slide.addShape('rect', {
      x: 0,
      y: 7.2,
      w: 13.33,
      h: 0.3,
      fill: { color: COLORS.SAFFRON },
      line: { color: COLORS.SAFFRON }
    });

    slide.addText('K. J. SOMAIYA COLLEGE OF ENGINEERING • DEVOPS INTERNAL ASSESSMENT', {
      x: 1.0,
      y: 1.3,
      w: 11.0,
      h: 0.3,
      fontSize: 12,
      fontFace: 'Arial',
      bold: true,
      color: COLORS.SAFFRON,
      charSpacing: 2
    });

    slide.addText('PostgreSQL Disaster Recovery\nUsing pgBackRest', {
      x: 1.0,
      y: 1.8,
      w: 11.3,
      h: 1.8,
      fontSize: 40,
      fontFace: 'Arial',
      bold: true,
      color: COLORS.TEXT_LIGHT,
      lineSpacing: 46
    });

    slide.addText('WAL Archiving, Point-in-Time Recovery (PITR) & Empirical Backup Strategy Evaluation', {
      x: 1.0,
      y: 3.8,
      w: 11.0,
      h: 0.6,
      fontSize: 18,
      fontFace: 'Arial',
      color: 'CBD5E1'
    });

    // Version Badges Card
    addCard(slide, 1.0, 4.7, 11.3, 1.8, COLORS.MAROON, '5B1A2E');

    slide.addText([
      { text: 'DEMONSTRATION PLATFORM: ', options: { bold: true, color: COLORS.SAFFRON, fontSize: 11 } },
      { text: 'StagePass Event Registration (Flagship: KJSCE Garba Eve, 12 Oct)\n', options: { color: COLORS.TEXT_LIGHT, fontSize: 11 } },
      { text: 'LAB INFRASTRUCTURE: ', options: { bold: true, color: COLORS.SAFFRON, fontSize: 11 } },
      { text: 'PostgreSQL 17.11  •  pgBackRest 2.59.3  •  Docker Compose Multi-Container Stack\n', options: { color: COLORS.TEXT_LIGHT, fontSize: 11 } },
      { text: 'CORE CAPABILITIES: ', options: { bold: true, color: COLORS.SAFFRON, fontSize: 11 } },
      { text: 'Zero Transaction Loss PITR  •  Guarded Archival LSN  •  Full / Diff / Incr Storage Benchmarks', options: { color: COLORS.TEXT_LIGHT, fontSize: 11 } }
    ], {
      x: 1.3,
      y: 4.9,
      w: 10.7,
      h: 1.4,
      fontFace: 'Arial',
      lineSpacing: 24
    });

    slide.addNotes('Welcome the evaluator. State topic, pinned versions (PostgreSQL 17.11, pgBackRest 2.59.3) and the StagePass scenario immediately.');
  }

  // ==========================================
  // SLIDE 2: THE PROBLEM (One Bad DELETE)
  // ==========================================
  {
    const slide = pptx.addSlide();
    slide.background = { color: COLORS.SURFACE_LIGHT };
    addHeader(slide, 'The Production Incident: Operator Error (Accidental DELETE)');

    // Left Card: Narrative
    addCard(slide, 0.8, 1.7, 6.8, 5.2);
    slide.addText('INCIDENT SCENARIO & BUSINESS IMPACT', {
      x: 1.1,
      y: 2.0,
      w: 6.2,
      h: 0.3,
      fontSize: 12,
      bold: true,
      color: COLORS.MAROON
    });

    slide.addText([
      { text: '• Context: ', options: { bold: true } },
      { text: 'Peak ticket booking window for the KJSCE Garba Eve flagship event.\n\n' },
      { text: '• Operator Catastrophe: ', options: { bold: true, color: COLORS.RED } },
      { text: 'A maintenance script issues an unconstrained SQL command:\n' },
      { text: '  DELETE FROM bookings WHERE event_id = 1;\n\n', options: { fontFace: 'Courier New', fontSize: 13, bold: true, color: COLORS.MAROON_DARK } },
      { text: '• Immediate Result: ', options: { bold: true } },
      { text: 'Total bookings plunge from 120 down to 80. All Garba bookings read exactly 0 on the live operations dashboard.\n\n' },
      { text: '• Engineering Mandate: ', options: { bold: true, color: COLORS.EMERALD } },
      { text: 'Restore service rapidly (minimize RTO) while preserving every single legitimate attendee transaction (minimize RPO).' }
    ], {
      x: 1.1,
      y: 2.4,
      w: 6.2,
      h: 4.2,
      fontSize: 14,
      fontFace: 'Arial',
      color: COLORS.TEXT_BODY,
      lineSpacing: 20
    });

    // Right Column: Metric Callout Cards
    // Metric 1: Loss Count
    addCard(slide, 7.9, 1.7, 4.6, 2.4, COLORS.RED_BG, 'FECACA');
    slide.addText('GARBA BOOKINGS AT INCIDENT', { x: 8.2, y: 1.9, w: 4.0, h: 0.3, fontSize: 11, bold: true, color: COLORS.RED });
    slide.addText('0', { x: 8.2, y: 2.2, w: 4.0, h: 1.0, fontSize: 54, bold: true, color: COLORS.RED });
    slide.addText('40 Confirmed Registrations Instantly Wiped', { x: 8.2, y: 3.3, w: 4.0, h: 0.5, fontSize: 12, color: COLORS.TEXT_DARK, bold: true });

    // Metric 2: Target Recovery
    addCard(slide, 7.9, 4.4, 4.6, 2.5, COLORS.EMERALD_BG, 'A7F3D0');
    slide.addText('RECOVERY CRITERIA (RPO = 0)', { x: 8.2, y: 4.6, w: 4.0, h: 0.3, fontSize: 11, bold: true, color: COLORS.EMERALD });
    slide.addText('120 / 120', { x: 8.2, y: 4.9, w: 4.0, h: 1.0, fontSize: 44, bold: true, color: COLORS.EMERALD });
    slide.addText('100% Transactions Preserved • 0 Orphans', { x: 8.2, y: 6.0, w: 4.0, h: 0.5, fontSize: 12, color: COLORS.TEXT_DARK, bold: true });

    slide.addNotes('Tell the incident story. Peak booking window, accidental DELETE runs, dashboard drops to 80/0. Point out the mandate: recover fast, lose zero registrations.');
  }

  // ==========================================
  // SLIDE 3: EVALUATOR VIEW (Live Dashboard Evidence)
  // ==========================================
  {
    const slide = pptx.addSlide();
    slide.background = { color: COLORS.SURFACE_LIGHT };
    addHeader(slide, 'Observable State: Live Operations Dashboard (/admin)');

    // Left: Description Card
    addCard(slide, 0.8, 1.7, 5.0, 5.2);
    slide.addText('REAL-TIME POSTGRESQL INTROSPECTION', {
      x: 1.1,
      y: 2.0,
      w: 4.4,
      h: 0.3,
      fontSize: 11,
      bold: true,
      color: COLORS.MAROON
    });

    slide.addText([
      { text: '• Non-Hardcoded Metrics:\n', options: { bold: true } },
      { text: 'Dashboard aggregates count directly from live PostgreSQL relations on every HTTP page load.\n\n' },
      { text: '• KPI Cards Track Recovery:\n', options: { bold: true } },
      { text: 'Tracks Total Bookings (120), Flagship Garba Count (40), and Event Capacity in real-time.\n\n' },
      { text: '• Audit Trail Verification:\n', options: { bold: true } },
      { text: 'Recent registrations list displays transaction IDs (bk_seed_... vs batch-registered IDs).\n\n' },
      { text: '• Immediate Incident Reflection:\n', options: { bold: true } },
      { text: 'When DELETE executes, this page visually crashes to 0 Garba bookings without caching.' }
    ], {
      x: 1.1,
      y: 2.4,
      w: 4.4,
      h: 4.2,
      fontSize: 13,
      fontFace: 'Arial',
      color: COLORS.TEXT_BODY,
      lineSpacing: 19
    });

    // Right: Screenshot
    const adminPath = path.join(ROOT, 'results', 'screenshots', 'admin.png');
    if (fs.existsSync(adminPath)) {
      addCard(slide, 6.1, 1.7, 6.4, 5.2, COLORS.SURFACE_CARD, COLORS.BORDER_CARD);
      slide.addImage({
        path: adminPath,
        x: 6.2,
        y: 1.8,
        w: 6.2,
        h: 4.5
      });
      slide.addText('Figure: Live StagePass Operations Center showing post-PITR state (120 Total, 40 Garba).', {
        x: 6.2,
        y: 6.4,
        w: 6.2,
        h: 0.4,
        fontSize: 10,
        italic: true,
        align: 'center',
        color: COLORS.TEXT_MUTED
      });
    }

    slide.addNotes('Point at the Garba KPI = 40 post-recovery. Stress that nothing is mocked; the web server queries PostgreSQL on every request.');
  }

  // ==========================================
  // SLIDE 4: RESEARCH QUESTION & OBJECTIVES
  // ==========================================
  {
    const slide = pptx.addSlide();
    slide.background = { color: COLORS.SURFACE_LIGHT };
    addHeader(slide, 'Research Question & Methodological Objectives');

    // Research Question Banner
    addCard(slide, 0.8, 1.7, 11.7, 1.5, COLORS.MAROON_DARK, COLORS.MAROON_DARK);
    slide.addText('CORE RESEARCH QUESTION', {
      x: 1.1,
      y: 1.85,
      w: 11.0,
      h: 0.25,
      fontSize: 10,
      bold: true,
      color: COLORS.SAFFRON,
      charSpacing: 2
    });
    slide.addText('“How does pgBackRest with archived WAL improve PostgreSQL recoverability after accidental data loss compared with a consistent file-system snapshot alone, and what are the time and storage trade-offs of its backup strategies?”', {
      x: 1.1,
      y: 2.15,
      w: 11.1,
      h: 0.9,
      fontSize: 15,
      fontFace: 'Arial',
      bold: true,
      color: COLORS.TEXT_LIGHT,
      lineSpacing: 21
    });

    // Three Objective Cards
    const objs = [
      {
        id: 'O1',
        title: 'Observable & Repeatable Lab',
        desc: 'Build StagePass containerized app, schema with constraints, deterministic 100-row seed and realistic HTTP workload runner.',
        target: 'Slide 6 & 8'
      },
      {
        id: 'O2',
        title: 'Controlled A/B Evaluation',
        desc: 'Execute identical 20-booking traffic & DELETE incident against Stopped Snapshot vs pgBackRest PITR. Measure exact data retention.',
        target: 'Slide 9 & 10'
      },
      {
        id: 'O3',
        title: 'Empirical Trade-off Matrix',
        desc: 'Quantify Full vs Differential vs Incremental backup speed, compression footprint, and pg_dump baseline on 20,000-row benchmarks.',
        target: 'Slide 7 & 11'
      }
    ];

    objs.forEach((o, i) => {
      const x = 0.8 + i * 4.0;
      addCard(slide, x, 3.4, 3.7, 3.5);

      // Objective Pill
      slide.addShape('roundRect', {
        x: x + 0.3,
        y: 3.7,
        w: 0.9,
        h: 0.4,
        rectRadius: 0.08,
        fill: { color: COLORS.MAROON },
        line: { color: COLORS.MAROON }
      });
      slide.addText(o.id, {
        x: x + 0.3,
        y: 3.7,
        w: 0.9,
        h: 0.4,
        fontSize: 12,
        bold: true,
        align: 'center',
        color: COLORS.TEXT_LIGHT
      });

      slide.addText(o.title, {
        x: x + 0.3,
        y: 4.3,
        w: 3.1,
        h: 0.6,
        fontSize: 14,
        bold: true,
        color: COLORS.MAROON_DARK
      });

      slide.addText(o.desc, {
        x: x + 0.3,
        y: 4.9,
        w: 3.1,
        h: 1.4,
        fontSize: 12,
        color: COLORS.TEXT_BODY,
        lineSpacing: 17
      });

      slide.addText(`Mapped to: ${o.target}`, {
        x: x + 0.3,
        y: 6.4,
        w: 3.1,
        h: 0.3,
        fontSize: 11,
        bold: true,
        color: COLORS.SAFFRON
      });
    });

    slide.addNotes('Read the RQ aloud verbatim. Map O1 to architecture & workload controls, O2 to the A/B recovery comparison, and O3 to the backup trade-off benchmark.');
  }

  // ==========================================
  // SLIDE 5: WHY SNAPSHOT-ONLY IS LIMITED
  // ==========================================
  {
    const slide = pptx.addSlide();
    slide.background = { color: COLORS.SURFACE_LIGHT };
    addHeader(slide, 'Theoretical Foundation: Physical Snapshot vs WAL Replay');

    // Left Column: Stopped Cluster Snapshot
    addCard(slide, 0.8, 1.7, 5.6, 5.2);
    slide.addText('BASELINE: STOPPED RSYNC SNAPSHOT', {
      x: 1.1,
      y: 2.0,
      w: 5.0,
      h: 0.3,
      fontSize: 12,
      bold: true,
      color: COLORS.RED
    });

    slide.addText([
      { text: '• Consistent Point-in-Time Image:\n', options: { bold: true } },
      { text: 'PostgreSQL daemon is cleanly stopped; PGDATA files mirrored with rsync -aHAX --delete.\n\n' },
      { text: '• Zero Post-Snapshot Visibility:\n', options: { bold: true, color: COLORS.RED } },
      { text: 'The snapshot freezes state at Time T. Without active WAL capture, any transaction written at T + 1 is permanently unrecoverable.\n\n' },
      { text: '• Fair Experimental Scope:\n', options: { bold: true } },
      { text: 'Rsync with manual WAL archival could do more, but enterprise teams frequently rely on storage snapshots alone—believing they suffice for disaster recovery.' }
    ], {
      x: 1.1,
      y: 2.4,
      w: 5.0,
      h: 4.2,
      fontSize: 13,
      fontFace: 'Arial',
      color: COLORS.TEXT_BODY,
      lineSpacing: 19
    });

    // Right Column: pgBackRest PITR
    addCard(slide, 6.8, 1.7, 5.7, 5.2, COLORS.EMERALD_BG, 'A7F3D0');
    slide.addText('CHAMPION: PGBACKREST + ARCHIVED WAL', {
      x: 7.1,
      y: 2.0,
      w: 5.1,
      h: 0.3,
      fontSize: 12,
      bold: true,
      color: COLORS.EMERALD
    });

    slide.addText([
      { text: '• Continuous WAL Stream:\n', options: { bold: true } },
      { text: 'PostgreSQL invokes archive_command on every 16 MB segment and archive_timeout threshold, shipping logs outside PGDATA.\n\n' },
      { text: '• Targeted Microsecond Replay:\n', options: { bold: true, color: COLORS.EMERALD } },
      { text: 'Restores base physical backup, then replays write-ahead logs up to a specific transaction, timestamp, or named restore point.\n\n' },
      { text: '• Resulting Paradigm Shift:\n', options: { bold: true } },
      { text: 'Shifts disaster recovery from "restore to backup time" to "restore to the exact microsecond before the disaster occurred".' }
    ], {
      x: 7.1,
      y: 2.4,
      w: 5.1,
      h: 4.2,
      fontSize: 13,
      fontFace: 'Arial',
      color: COLORS.TEXT_BODY,
      lineSpacing: 19
    });

    slide.addNotes('Defuse the "rsync is bad" misreading: stopped rsync is perfectly consistent at time T. But snapshot-only cannot replay subsequent transactions without archived WAL.');
  }

  // ==========================================
  // SLIDE 6: ARCHITECTURE
  // ==========================================
  {
    const slide = pptx.addSlide();
    slide.background = { color: COLORS.SURFACE_LIGHT };
    addHeader(slide, 'System Architecture: Isolation, Archival & Promotion');

    // Architecture Diagram flow boxes
    const nodes = [
      {
        title: 'StagePass App',
        sub: 'FastAPI / Jinja2 (:8000)',
        desc: 'Request-scoped pooling\nSurvives DB downtime',
        color: COLORS.MAROON_DARK,
        x: 0.8
      },
      {
        title: 'PostgreSQL 17.11',
        sub: 'Database Engine (:5433)',
        desc: 'wal_level=replica\narchive_mode=on',
        color: COLORS.MAROON,
        x: 3.8
      },
      {
        title: 'Dedicated Repo',
        sub: 'Docker Volume (/var/lib/pbr)',
        desc: 'Isolated from PGDATA\nFull/Diff/Incr + WAL',
        color: COLORS.SLATE_CARD,
        x: 6.8
      },
      {
        title: 'Backup-Tools',
        sub: 'Operational Sidecar',
        desc: 'Guarded restore CLI\nLSN verification gates',
        color: COLORS.EMERALD,
        x: 9.8
      }
    ];

    nodes.forEach(n => {
      addCard(slide, n.x, 1.8, 2.7, 3.2, COLORS.SURFACE_CARD, COLORS.BORDER_CARD);

      slide.addShape('roundRect', {
        x: n.x + 0.2,
        y: 2.0,
        w: 2.3,
        h: 0.6,
        rectRadius: 0.05,
        fill: { color: n.color },
        line: { color: n.color }
      });

      slide.addText(n.title, {
        x: n.x + 0.2,
        y: 2.0,
        w: 2.3,
        h: 0.35,
        fontSize: 12,
        bold: true,
        align: 'center',
        color: COLORS.TEXT_LIGHT
      });

      slide.addText(n.sub, {
        x: n.x + 0.2,
        y: 2.35,
        w: 2.3,
        h: 0.25,
        fontSize: 9,
        align: 'center',
        color: COLORS.SAFFRON_LIGHT
      });

      slide.addText(n.desc, {
        x: n.x + 0.2,
        y: 2.8,
        w: 2.3,
        h: 2.0,
        fontSize: 11,
        align: 'center',
        color: COLORS.TEXT_BODY,
        lineSpacing: 16
      });
    });

    // Flow Arrows / Connections Card below
    addCard(slide, 0.8, 5.3, 11.7, 1.6, COLORS.SLATE_BG, COLORS.SLATE_BG);

    slide.addText('SAFETY BY DESIGN: VOLUME ISOLATION & SHORT-LIVED SESSIONS', {
      x: 1.1,
      y: 5.5,
      w: 11.0,
      h: 0.25,
      fontSize: 10,
      bold: true,
      color: COLORS.SAFFRON,
      charSpacing: 1.5
    });

    slide.addText([
      { text: '1. Separate Repository Volume: ', options: { bold: true, color: COLORS.TEXT_LIGHT } },
      { text: 'PGDATA and pgBackRest repository live on separate Docker volumes; restore never overwrites backup storage.\n' },
      { text: '2. Connection Resilience: ', options: { bold: true, color: COLORS.TEXT_LIGHT } },
      { text: 'FastAPI uses scoped sessions; when DB restarts during restore, requests fail gracefully and reconnect instantly.\n' },
      { text: '3. Guarded Scripts: ', options: { bold: true, color: COLORS.TEXT_LIGHT } },
      { text: 'Strict checks verify stanza health, LSN archival status, and container state before triggering commands.' }
    ], {
      x: 1.1,
      y: 5.8,
      w: 11.0,
      h: 1.0,
      fontSize: 11,
      color: 'CBD5E1',
      lineSpacing: 16
    });

    slide.addNotes('Trace the data flow: app writes to DB, WAL is pushed to repository volume, backup-tools controls PITR restore and signals promotion.');
  }

  // ==========================================
  // SLIDE 7: BACKUP MODES + NAMED PITR
  // ==========================================
  {
    const slide = pptx.addSlide();
    slide.background = { color: COLORS.SURFACE_LIGHT };
    addHeader(slide, 'Backup Strategies & Self-Documenting Named PITR');

    // 3 Cards for Modes
    const modes = [
      {
        name: 'FULL BACKUP',
        dur: '10.6 s',
        size: '4.5 MB',
        ratio: '100% Base',
        note: 'Complete physical cluster copy + active WAL. Self-contained; highest time & storage cost.',
        color: COLORS.MAROON
      },
      {
        name: 'DIFFERENTIAL',
        dur: '2.5 s',
        size: '697.7 KB',
        ratio: '84.5% Reduction',
        note: 'Copies all changed pages since the last FULL backup. Breaks dependency on prior incrementals.',
        color: COLORS.GOLD
      },
      {
        name: 'INCREMENTAL',
        dur: '3.0 s',
        size: '635.8 KB',
        ratio: '85.9% Reduction',
        note: 'Copies only blocks modified since ANY last backup. Fastest routine cycle; chained dependency.',
        color: COLORS.EMERALD
      }
    ];

    modes.forEach((m, i) => {
      const x = 0.8 + i * 4.0;
      addCard(slide, x, 1.7, 3.7, 3.1);

      slide.addText(m.name, {
        x: x + 0.3,
        y: 1.9,
        w: 3.1,
        h: 0.3,
        fontSize: 12,
        bold: true,
        color: m.color
      });

      slide.addText(m.dur, {
        x: x + 0.3,
        y: 2.2,
        w: 1.5,
        h: 0.6,
        fontSize: 26,
        bold: true,
        color: COLORS.TEXT_DARK
      });

      slide.addText(m.size, {
        x: x + 1.8,
        y: 2.2,
        w: 1.6,
        h: 0.6,
        fontSize: 22,
        bold: true,
        color: COLORS.TEXT_MUTED
      });

      slide.addShape('roundRect', {
        x: x + 0.3,
        y: 2.85,
        w: 3.1,
        h: 0.35,
        rectRadius: 0.05,
        fill: { color: COLORS.SURFACE_LIGHT },
        line: { color: COLORS.BORDER_CARD }
      });

      slide.addText(`Storage Efficiency: ${m.ratio}`, {
        x: x + 0.3,
        y: 2.85,
        w: 3.1,
        h: 0.35,
        fontSize: 10,
        bold: true,
        align: 'center',
        color: COLORS.TEXT_BODY
      });

      slide.addText(m.note, {
        x: x + 0.3,
        y: 3.3,
        w: 3.1,
        h: 1.3,
        fontSize: 11,
        color: COLORS.TEXT_MUTED,
        lineSpacing: 15
      });
    });

    // Bottom Named PITR Card
    addCard(slide, 0.8, 5.1, 11.7, 1.8, COLORS.SURFACE_CARD, COLORS.BORDER_CARD);
    slide.addText('NAMED RECOVERY TARGETS (SELF-DOCUMENTING AUDIT TRAIL)', {
      x: 1.1,
      y: 5.3,
      w: 11.0,
      h: 0.3,
      fontSize: 11,
      bold: true,
      color: COLORS.MAROON
    });

    slide.addText([
      { text: '• Elimination of Clock Skew: ', options: { bold: true } },
      { text: 'Instead of ambiguous timestamps, we plant a named restore point via SELECT pg_create_restore_point(\'rp_scenario_b\');\n' },
      { text: '• Guaranteed Archival Gate: ', options: { bold: true, color: COLORS.EMERALD } },
      { text: 'Recovery script queries WAL segment archives and refuses to restore until the exact LSN is proven safely written to repository disk.\n' },
      { text: '• Precise Target Recovery: ', options: { bold: true } },
      { text: 'pgbackrest restore --type=name --target=rp_scenario_b --target-action=promote replays up to the point and reopens DB for read-write.' }
    ], {
      x: 1.1,
      y: 5.65,
      w: 11.0,
      h: 1.1,
      fontSize: 11,
      color: COLORS.TEXT_BODY,
      lineSpacing: 16
    });

    slide.addNotes('Stress that sizes are compressed repository bytes, not raw DB megabytes. Highlight the named restore point and the safety gate preventing restore until WAL is archived.');
  }

  // ==========================================
  // SLIDE 8: STAGEPASS CONTROLS & METHODOLOGY
  // ==========================================
  {
    const slide = pptx.addSlide();
    slide.background = { color: COLORS.SURFACE_LIGHT };
    addHeader(slide, 'Experimental Controls & Repeatability Rigor');

    // Left Column: Methodological Controls
    addCard(slide, 0.8, 1.7, 5.0, 5.2);
    slide.addText('METHODOLOGICAL GUARDS & INVARIANTS', {
      x: 1.1,
      y: 2.0,
      w: 4.4,
      h: 0.3,
      fontSize: 11,
      bold: true,
      color: COLORS.MAROON
    });

    slide.addText([
      { text: '• Deterministic 100-Row Seed:\n', options: { bold: true } },
      { text: 'Fixed distribution (20 Garba, 50 TechSummit, 30 MusicFest) seeded identically for both scenarios.\n\n' },
      { text: '• Identical 20-HTTP Workload:\n', options: { bold: true } },
      { text: '20 real HTTP registration payloads executed via scripts/workload.py against /api/events/kjsce-garba-eve/register.\n\n' },
      { text: '• Two-Phase Replication (Run 1 & Run 2):\n', options: { bold: true } },
      { text: 'Every test run twice from scratch with isolated run IDs, raw CSV logs, and terminal recordings.\n\n' },
      { text: '• Automated Invariant Checking:\n', options: { bold: true } },
      { text: 'Automated test suite (8 pytest tests) validates database constraints, transaction isolation, and health endpoints.' }
    ], {
      x: 1.1,
      y: 2.4,
      w: 4.4,
      h: 4.2,
      fontSize: 12.5,
      fontFace: 'Arial',
      color: COLORS.TEXT_BODY,
      lineSpacing: 18
    });

    // Right: Home Screenshot
    const homePath = path.join(ROOT, 'results', 'screenshots', 'home.png');
    if (fs.existsSync(homePath)) {
      addCard(slide, 6.1, 1.7, 6.4, 5.2, COLORS.SURFACE_CARD, COLORS.BORDER_CARD);
      slide.addImage({
        path: homePath,
        x: 6.2,
        y: 1.8,
        w: 6.2,
        h: 4.5
      });
      slide.addText('Figure: StagePass Home UI featuring Garba Eve (12 OCT badge, live status pill, real registration modal).', {
        x: 6.2,
        y: 6.4,
        w: 6.2,
        h: 0.4,
        fontSize: 10,
        italic: true,
        align: 'center',
        color: COLORS.TEXT_MUTED
      });
    }

    slide.addNotes('Show home screenshot with 12 OCT badge and live pill. Mention that seed is always 100 bookings and both scenarios receive the identical 20 HTTP registrations.');
  }

  // ==========================================
  // SLIDE 9: SCENARIO A RESULT (Snapshot Baseline)
  // ==========================================
  {
    const slide = pptx.addSlide();
    slide.background = { color: COLORS.SURFACE_LIGHT };
    addHeader(slide, 'Scenario A: Stopped Rsync Snapshot Alone (Data Loss)');

    // Left Column: Result Breakdown
    addCard(slide, 0.8, 1.7, 6.0, 5.2);
    slide.addText('EXECUTION TIMELINE & DATA RECOVERY GAP', {
      x: 1.1,
      y: 2.0,
      w: 5.4,
      h: 0.3,
      fontSize: 11,
      bold: true,
      color: COLORS.RED
    });

    slide.addText([
      { text: '1. Baseline Snapshot Taken: ', options: { bold: true } },
      { text: 'Cluster stopped, rsync snapshot created at 100 bookings (20 Garba).\n\n' },
      { text: '2. Live Traffic Ingestion: ', options: { bold: true } },
      { text: '20 valid attendees register via HTTP; database count climbs to 120 (40 Garba).\n\n' },
      { text: '3. Disaster Triggered: ', options: { bold: true, color: COLORS.RED } },
      { text: 'DELETE query wipes all Garba Eve registrations; count plunges to 80.\n\n' },
      { text: '4. Disaster Recovery Restored: ', options: { bold: true } },
      { text: 'Cluster stopped, rsync snapshot restored, PostgreSQL restarted.\n\n' },
      { text: '• Final Evaluated State: ', options: { bold: true, color: COLORS.RED } },
      { text: '100 Total / 20 Garba. Exactly ZERO of the 20 post-snapshot registrations survived.' }
    ], {
      x: 1.1,
      y: 2.4,
      w: 5.4,
      h: 4.2,
      fontSize: 13,
      fontFace: 'Arial',
      color: COLORS.TEXT_BODY,
      lineSpacing: 19
    });

    // Right Column: Metric Callout Cards
    addCard(slide, 7.1, 1.7, 5.4, 2.4, COLORS.RED_BG, 'FECACA');
    slide.addText('TRANSACTIONS PRESERVED (RPO)', { x: 7.4, y: 1.9, w: 4.8, h: 0.3, fontSize: 11, bold: true, color: COLORS.RED });
    slide.addText('0 / 20 (0%)', { x: 7.4, y: 2.2, w: 4.8, h: 0.9, fontSize: 44, bold: true, color: COLORS.RED });
    slide.addText('20 Legitimate Registrations Permanently Lost', { x: 7.4, y: 3.2, w: 4.8, h: 0.4, fontSize: 12, bold: true, color: COLORS.TEXT_DARK });

    addCard(slide, 7.1, 4.4, 5.4, 2.5, COLORS.SURFACE_CARD, COLORS.BORDER_CARD);
    slide.addText('MEASURED TIME METRICS (RUN 1 & 2)', { x: 7.4, y: 4.6, w: 4.8, h: 0.3, fontSize: 11, bold: true, color: COLORS.MAROON });

    slide.addText([
      { text: '• Snapshot Duration: ', options: { bold: true } },
      { text: '0.5 s – 1.1 s (local storage copy)\n\n' },
      { text: '• Recovery Time Objective (RTO): ', options: { bold: true } },
      { text: '10.6 s – 15.0 s\n\n' },
      { text: '• Verdict: ', options: { bold: true, color: COLORS.RED } },
      { text: 'Fast recovery, but unacceptable RPO breach for active online services.' }
    ], {
      x: 7.4,
      y: 5.0,
      w: 4.8,
      h: 1.8,
      fontSize: 12.5,
      color: COLORS.TEXT_BODY,
      lineSpacing: 18
    });

    slide.addNotes('Snapshot, 20 registrations, DELETE, restore: back to 100, Garba 20, zero of the new twenty survive. Correct behavior for snapshot alone, but lossy.');
  }

  // ==========================================
  // SLIDE 10: SCENARIO B RESULT (pgBackRest PITR)
  // ==========================================
  {
    const slide = pptx.addSlide();
    slide.background = { color: COLORS.SURFACE_LIGHT };
    addHeader(slide, 'Scenario B: pgBackRest with Archived WAL (100% Recovery)');

    // Left Column: Result Breakdown
    addCard(slide, 0.8, 1.7, 6.0, 5.2, COLORS.EMERALD_BG, 'A7F3D0');
    slide.addText('EXECUTION TIMELINE & AUDIT RECORD', {
      x: 1.1,
      y: 2.0,
      w: 5.4,
      h: 0.3,
      fontSize: 11,
      bold: true,
      color: COLORS.EMERALD
    });

    slide.addText([
      { text: '1. Online Base Backup: ', options: { bold: true } },
      { text: 'pgBackRest creates hot physical backup at 100 bookings.\n\n' },
      { text: '2. Live Traffic & Named Restore Point: ', options: { bold: true } },
      { text: '20 attendees register (120 total / 40 Garba). Restore point rp_scenario_b planted with logged LSN.\n\n' },
      { text: '3. Verified WAL Archival Guard: ', options: { bold: true, color: COLORS.EMERALD } },
      { text: 'Script verifies target segment is pushed to repo before proceeding.\n\n' },
      { text: '4. Disaster & Target PITR Restore: ', options: { bold: true } },
      { text: 'Accidental DELETE wipes Garba. pgBackRest restores base backup, configures recovery target, replays WAL, and promotes.\n\n' },
      { text: '• Final Evaluated State: ', options: { bold: true, color: COLORS.EMERALD } },
      { text: '120 Total / 40 Garba. Exactly 20/20 new registrations fully recovered!' }
    ], {
      x: 1.1,
      y: 2.4,
      w: 5.4,
      h: 4.2,
      fontSize: 13,
      fontFace: 'Arial',
      color: COLORS.TEXT_BODY,
      lineSpacing: 19
    });

    // Right Column: Metric Callout Cards
    addCard(slide, 7.1, 1.7, 5.4, 2.4, COLORS.SURFACE_CARD, 'A7F3D0');
    slide.addText('TRANSACTIONS PRESERVED (RPO)', { x: 7.4, y: 1.9, w: 4.8, h: 0.3, fontSize: 11, bold: true, color: COLORS.EMERALD });
    slide.addText('20 / 20 (100%)', { x: 7.4, y: 2.2, w: 4.8, h: 0.9, fontSize: 44, bold: true, color: COLORS.EMERALD });
    slide.addText('Zero Data Loss • All Transaction IDs Intact', { x: 7.4, y: 3.2, w: 4.8, h: 0.4, fontSize: 12, bold: true, color: COLORS.TEXT_DARK });

    addCard(slide, 7.1, 4.4, 5.4, 2.5, COLORS.SURFACE_CARD, COLORS.BORDER_CARD);
    slide.addText('PERFORMANCE & AUDIT VALIDATION', { x: 7.4, y: 4.6, w: 4.8, h: 0.3, fontSize: 11, bold: true, color: COLORS.MAROON });

    slide.addText([
      { text: '• Recovery Time Objective (RTO): ', options: { bold: true } },
      { text: '17.6 s – 20.6 s (only ~5s more than snapshot)\n\n' },
      { text: '• Engine Confirmation: ', options: { bold: true } },
      { text: 'PostgreSQL engine log explicitly confirms:\n' },
      { text: '  "recovery stopping at restore point \"rp_scenario_b\""\n\n', options: { fontFace: 'Courier New', fontSize: 10, bold: true, color: COLORS.MAROON } },
      { text: '• Reproducibility: ', options: { bold: true } },
      { text: '100% verified across both independent experimental runs.' }
    ], {
      x: 7.4,
      y: 5.0,
      w: 4.8,
      h: 1.8,
      fontSize: 12,
      color: COLORS.TEXT_BODY,
      lineSpacing: 17
    });

    slide.addNotes('Full backup, 20 registrations, named restore point, verified archival, DELETE, restore to name, promote. Engine logs confirm target. All 20 IDs back.');
  }

  // ==========================================
  // SLIDE 11: EVALUATION & BENCHMARKS
  // ==========================================
  {
    const slide = pptx.addSlide();
    slide.background = { color: COLORS.SURFACE_LIGHT };
    addHeader(slide, 'Quantitative Evaluation: RTO, RPO & Storage Trade-offs');

    // Embed Generated Plots Side-by-Side
    const plotRecovery = path.join(ROOT, 'results', 'plots', 'recovery_counts.png');
    const plotBackup = path.join(ROOT, 'results', 'plots', 'backup_durations.png');

    if (fs.existsSync(plotRecovery)) {
      addCard(slide, 0.8, 1.7, 5.7, 3.5);
      slide.addImage({ path: plotRecovery, x: 0.9, y: 1.8, w: 5.5, h: 3.3 });
    }

    if (fs.existsSync(plotBackup)) {
      addCard(slide, 6.8, 1.7, 5.7, 3.5);
      slide.addImage({ path: plotBackup, x: 6.9, y: 1.8, w: 5.5, h: 3.3 });
    }

    // Bottom Comparative Summary Table
    addCard(slide, 0.8, 5.4, 11.7, 1.6, COLORS.SURFACE_CARD, COLORS.BORDER_CARD);
    slide.addText('EMPIRICAL TRADE-OFF SUMMARY (MEASURED REAL DATA)', {
      x: 1.1,
      y: 5.55,
      w: 11.0,
      h: 0.25,
      fontSize: 10,
      bold: true,
      color: COLORS.MAROON,
      charSpacing: 1.5
    });

    slide.addText([
      { text: '• RTO Comparison: ', options: { bold: true } },
      { text: 'Snapshot RTO is 10.6–15.0 s vs pgBackRest PITR at 17.6–20.6 s (a modest ~5–7 s difference for WAL replay).\n' },
      { text: '• RPO Comparison: ', options: { bold: true } },
      { text: 'Snapshot loses 20 transactions (100% loss of unbacked traffic); pgBackRest achieves 0 data loss.\n' },
      { text: '• Storage Optimization: ', options: { bold: true } },
      { text: 'Differential and incremental modes slash routine backup time from 10.6 s down to 2.5–3.0 s, saving >84% repository space.' }
    ], {
      x: 1.1,
      y: 5.85,
      w: 11.0,
      h: 1.0,
      fontSize: 11,
      color: COLORS.TEXT_BODY,
      lineSpacing: 16
    });

    slide.addNotes('RTO differs by seconds (11-15s vs 18-21s). Recoverability differs by 20 transactions. Point at the charts: real benchmark numbers from CSV.');
  }

  // ==========================================
  // SLIDE 12: CONCLUSION & REFERENCES
  // ==========================================
  {
    const slide = pptx.addSlide();
    slide.background = { color: COLORS.MAROON_DARK };

    // Decorative top border
    slide.addShape('rect', {
      x: 0,
      y: 0,
      w: 13.33,
      h: 0.15,
      fill: { color: COLORS.SAFFRON },
      line: { color: COLORS.SAFFRON }
    });

    addHeader(slide, 'Conclusion, Threats to Validity & Academic References', 'SYNTHESIS & CLOSING', true);

    // Left Column: Key Takeaway Box
    addCard(slide, 0.8, 1.7, 6.0, 5.2, COLORS.MAROON, '5B1A2E');
    slide.addText('CORE FINDINGS & SCIENTIFIC ANSWER', {
      x: 1.1,
      y: 2.0,
      w: 5.4,
      h: 0.3,
      fontSize: 11,
      bold: true,
      color: COLORS.SAFFRON
    });

    slide.addText([
      { text: '1. Recoverability Advantage: ', options: { bold: true, color: COLORS.TEXT_LIGHT } },
      { text: 'pgBackRest + archived WAL elevates recovery from "state at backup time" to "state at chosen target", preventing data loss from operator errors.\n\n', options: { color: 'E2E8F0' } },
      { text: '2. Backup Strategy Trade-offs: ', options: { bold: true, color: COLORS.TEXT_LIGHT } },
      { text: 'Differential & incremental modes reduce routine overhead by ~85% in size and ~75% in runtime, making frequent protection practical.\n\n', options: { color: 'E2E8F0' } },
      { text: '3. Honest Limitations: ', options: { bold: true, color: COLORS.TEXT_LIGHT } },
      { text: 'Lab conducted on single-host Docker; production requires off-site S3 storage, standby instances, and automated archive lag alerting.', options: { color: 'E2E8F0' } }
    ], {
      x: 1.1,
      y: 2.4,
      w: 5.4,
      h: 4.2,
      fontSize: 12.5,
      fontFace: 'Arial',
      lineSpacing: 18
    });

    // Right Column: Official References
    addCard(slide, 7.1, 1.7, 5.4, 5.2, COLORS.SLATE_CARD, '475569');
    slide.addText('PRIMARY DOCUMENTATION REFERENCES', {
      x: 7.4,
      y: 2.0,
      w: 4.8,
      h: 0.3,
      fontSize: 11,
      bold: true,
      color: COLORS.SAFFRON
    });

    slide.addText([
      { text: '[1] pgBackRest User Guide & Command Reference\n', options: { bold: true, color: COLORS.TEXT_LIGHT } },
      { text: 'https://pgbackrest.org/user-guide.html (v2.59.3)\n\n', options: { color: '94A3B8', fontSize: 10 } },
      { text: '[2] PostgreSQL 17 Backup and Restore Documentation\n', options: { bold: true, color: COLORS.TEXT_LIGHT } },
      { text: 'https://www.postgresql.org/docs/17/backup.html\n\n', options: { color: '94A3B8', fontSize: 10 } },
      { text: '[3] Continuous Archiving and Point-in-Time Recovery\n', options: { bold: true, color: COLORS.TEXT_LIGHT } },
      { text: 'https://www.postgresql.org/docs/17/continuous-archiving.html\n\n', options: { color: '94A3B8', fontSize: 10 } },
      { text: '• Full Reproducibility: ', options: { bold: true, color: COLORS.SAFFRON } },
      { text: 'All scripts, Makefile targets, and raw CSV runs available in repository.', options: { color: 'E2E8F0', fontSize: 11 } }
    ], {
      x: 7.4,
      y: 2.4,
      w: 4.8,
      h: 4.2,
      fontSize: 11.5,
      fontFace: 'Arial',
      lineSpacing: 16
    });

    slide.addNotes('Summarize the core answer to the RQ. Point to pgbackrest.org and postgresql.org references. Offer to run either scenario live via Makefile.');
  }

  await pptx.writeFile({ fileName: OUTPUT_PATH });
  console.log(`SUCCESS: Modern 12-slide presentation generated via PptxGenJS at: ${OUTPUT_PATH}`);
}

buildPresentation().catch(err => {
  console.error("Error building presentation:", err);
  process.exit(1);
});
