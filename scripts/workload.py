"""Deterministic HTTP workload: N registrations to a given event slug via the StagePass API."""
import argparse
import csv
import json
import os
import sys
import time
import urllib.request

APP_URL = os.environ.get("APP_URL", "http://localhost:8000")


def post_register(slug, name, email, tickets, batch):
    body = json.dumps({"name": name, "email": email, "tickets": tickets,
                       "simulation_batch_id": batch}).encode()
    req = urllib.request.Request(f"{APP_URL}/api/events/{slug}/register", data=body,
                                 headers={"Content-Type": "application/json"}, method="POST")
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode())
            return r.status, data, time.time() - t0
    except Exception as e:  # noqa: BLE001
        # try to extract HTTPError body
        try:
            data = json.loads(e.read().decode())  # type: ignore[attr-defined]
            return e.code, data, time.time() - t0  # type: ignore[attr-defined]
        except Exception:
            return 0, {"error": str(e)[:200]}, time.time() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", default="kjsce-garba-eve")
    ap.add_argument("--count", type=int, default=20)
    ap.add_argument("--batch", default="post-backup-run1")
    ap.add_argument("--start-index", type=int, default=1)
    ap.add_argument("--out", default="results/registration_requests.csv")
    ap.add_argument("--scenario", default="manual")
    args = ap.parse_args()

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    new_file = not os.path.exists(args.out)
    rows = []
    with open(args.out, "a", newline="") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow(["scenario_id", "request_no", "email", "http_status",
                        "booking_id", "duration_s", "timestamp"])
        for i in range(args.count):
            idx = args.start_index + i
            email = f"attendee{idx:03d}@example.test"
            name = f"Load Attendee {idx:03d}"
            st, data, dur = post_register(args.slug, name, email, 1 + (idx % 2), args.batch)
            ts = time.strftime("%Y-%m-%dT%H:%M:%S")
            bid = data.get("booking_id", "") if isinstance(data, dict) else ""
            w.writerow([args.scenario, i + 1, email, st, bid, f"{dur:.3f}", ts])
            f.flush()
            print(f"[{i+1}/{args.count}] {email} -> {st} {bid} ({dur:.2f}s)", flush=True)
            rows.append((st, bid))
    failed = [r for r in rows if r[0] != 200 or not r[1]]
    if failed:
        print(f"WORKLOAD FAILED: {len(failed)}/{len(rows)} requests did not succeed", flush=True)
        sys.exit(1)
    print(f"WORKLOAD OK: {len(rows)} registrations batch={args.batch}", flush=True)


if __name__ == "__main__":
    main()
