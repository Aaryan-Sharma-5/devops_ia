"""Generate comparison charts from recorded CSVs (never hand-typed numbers).

Reads results/experiment_runs.csv + results/backup_benchmarks.csv and writes
results/plots/*.png using matplotlib (pip install matplotlib if missing).
Falls back to simple SVG bars if matplotlib is unavailable.
"""
import csv
import os
import sys

PLOTDIR = "results/plots"


def read_runs(path="results/experiment_runs.csv"):
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path) as f:
        rows.extend(csv.DictReader(f))
    return rows


def read_bench(path="results/backup_benchmarks.csv"):
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path) as f:
        rows.extend(csv.DictReader(f))
    return rows


def svg_bars(path, title, series):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    mx = max((v for _, v in series), default=1) or 1
    bars = ""
    for i, (k, v) in enumerate(series):
        w = 380 * v / mx
        y = 30 + i * 34
        bars += (f'<text x="5" y="{y+14}" font-size="12">{k} ({v})</text>'
                 f'<rect x="210" y="{y}" width="{w:.0f}" height="18" fill="#7a2a44"/>')
    h = 50 + len(series) * 34
    with open(path, "w") as f:
        f.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="640" height="{h}">'
                f'<text x="5" y="18" font-size="14" font-weight="bold">{title}</text>{bars}</svg>')
    print(f"wrote {path}", flush=True)


def main():
    os.makedirs(PLOTDIR, exist_ok=True)
    runs = read_runs()
    bench = read_bench()
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        has_mpl = True
    except ImportError:
        print("matplotlib missing — writing SVG fallbacks (pip install matplotlib for PNGs)", flush=True)
        has_mpl = False

    # Chart 1: recovery counts per scenario (baseline / pre / recovered)
    if runs:
        if has_mpl:
            labels, base, pre, rec = [], [], [], []
            for r in runs:
                labels.append(r.get("scenario_id", "?"))
                base.append(int(r.get("baseline_booking_count") or 0))
                pre.append(int(r.get("pre_incident_booking_count") or 0))
                rec.append(int(r.get("recovered_booking_count") or 0))
            x = range(len(labels))
            w = 0.25
            plt.figure(figsize=(8, 4.5))
            plt.bar([i - w for i in x], base, w, label="baseline")
            plt.bar(x, pre, w, label="pre-incident")
            plt.bar([i + w for i in x], rec, w, label="recovered")
            plt.xticks(list(x), labels, rotation=15)
            plt.ylabel("bookings")
            plt.title("Snapshot-only vs PITR: booking counts (from experiment_runs.csv)")
            plt.legend()
            plt.tight_layout()
            plt.savefig(f"{PLOTDIR}/recovery_counts.png")
            print(f"wrote {PLOTDIR}/recovery_counts.png", flush=True)
        else:
            for r in runs:
                svg_bars(f"{PLOTDIR}/{r.get('scenario_id','run')}_counts.svg",
                         f"{r.get('scenario_id')} counts",
                         [("baseline", int(r.get("baseline_booking_count") or 0)),
                          ("pre-incident", int(r.get("pre_incident_booking_count") or 0)),
                          ("recovered", int(r.get("recovered_booking_count") or 0))])
    else:
        print("no experiment_runs.csv yet — skipping recovery chart", flush=True)

    # Chart 2: backup durations by type (single trial)
    if bench:
        agg = {}
        for b in bench:
            try:
                agg.setdefault(b["backup_type"], []).append(float(b["duration_s"]))
            except (KeyError, ValueError):
                pass
        med = {k: sorted(v)[len(v) // 2] for k, v in agg.items()}
        if has_mpl:
            import matplotlib.pyplot as plt
            plt.figure(figsize=(7, 4))
            plt.bar(list(med.keys()), list(med.values()), color=["#5b1a2e", "#e8a13c", "#e0683c"][:len(med)])
            plt.ylabel("measured duration in seconds (single trial)")
            plt.title("pgBackRest backup durations by type (measured single trial)")
            plt.tight_layout()
            plt.savefig(f"{PLOTDIR}/backup_durations.png")
            plt.close()
            print(f"wrote {PLOTDIR}/backup_durations.png", flush=True)

            # Chart 3: Storage comparison - Individual backup size vs Cumulative repository size
            types = [b.get("backup_type") for b in bench]
            backup_sizes_mb = [float(b.get("backup_size_bytes", 0)) / (1024 * 1024) for b in bench]
            repo_totals_mb = [float(b.get("repository_total_bytes_after", 0)) / (1024 * 1024) for b in bench]
            x = range(len(types))
            w = 0.35
            plt.figure(figsize=(7.5, 4.5))
            b1 = plt.bar([i - w / 2 for i in x], backup_sizes_mb, w, label="Individual Backup Size (MiB)", color="#e0683c")
            b2 = plt.bar([i + w / 2 for i in x], repo_totals_mb, w, label="Cumulative Repository Total (MiB)", color="#5b1a2e")
            for bar in b1:
                yval = bar.get_height()
                plt.text(bar.get_x() + bar.get_width() / 2.0, yval + 0.2, f"{yval:.2f} MiB", ha='center', va='bottom', fontsize=8, color='#334155')
            for bar in b2:
                yval = bar.get_height()
                plt.text(bar.get_x() + bar.get_width() / 2.0, yval + 0.2, f"{yval:.2f} MiB", ha='center', va='bottom', fontsize=8, color='#334155')
            plt.xticks(list(x), [t.capitalize() for t in types])
            plt.ylabel("Size (MiB)")
            plt.ylim(0, max(repo_totals_mb) * 1.15)
            plt.title("pgBackRest Storage: Backup Size vs Cumulative Repository Size")
            plt.legend()
            plt.tight_layout()
            plt.savefig(f"{PLOTDIR}/backup_storage.png")
            plt.close()
            print(f"wrote {PLOTDIR}/backup_storage.png", flush=True)
        else:
            svg_bars(f"{PLOTDIR}/backup_durations.svg", "backup durations (measured single trial s)",
                     [(k, round(v, 1)) for k, v in med.items()])
    else:
        print("no backup_benchmarks.csv yet — skipping duration chart", flush=True)


if __name__ == "__main__":
    sys.exit(main())
