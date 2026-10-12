"""Safety guards for all destructive operations (lab-only)."""
import os
import sys

LAB_FLAG = os.environ.get("STAGEPASS_LAB", "")
DATABASE_URL = os.environ.get("DATABASE_URL", "")
FORBIDDEN_DESTS = {"", "/", "/var/lib/postgresql", "/var/lib/postgresql/data", "/etc", "/root", "/home"}
FORBIDDEN_SUBSTR = ["/home/anamay", "/var/lib/postgresql/main"]


def require_lab(dbname: str = "stagepass"):
    if LAB_FLAG != "1":
        sys.exit("REFUSED: STAGEPASS_LAB!=1. Destructive ops only in the lab container/project.")
    url = DATABASE_URL or ""
    if dbname not in url and url:
        sys.exit(f"REFUSED: DATABASE_URL does not reference lab db '{dbname}': {url.split('@')[-1]}")
    if "prod" in url.lower():
        sys.exit("REFUSED: URL looks like production.")


def validate_rsync_paths(src: str, dst: str):
    for p in (src, dst):
        if not p or p.strip() == "":
            sys.exit(f"REFUSED: empty rsync path (src={src!r} dst={dst!r})")
    if dst.strip() in FORBIDDEN_DESTS or src.strip() in FORBIDDEN_DESTS:
        sys.exit(f"REFUSED: forbidden rsync path src={src!r} dst={dst!r}")
    for bad in FORBIDDEN_SUBSTR:
        if dst.startswith(bad):
            sys.exit(f"REFUSED: destination under host path {bad!r}")
    # Snapshot/restore must stay inside the lab volumes
    ok_prefix = ("/snapshots", "/var/lib/postgresql/data")
    if not (dst.startswith(ok_prefix) or "/snapshots/" in dst or "snapshot" in dst):
        # allow pgdata restore target explicitly
        if dst not in ("/var/lib/postgresql/data/pgdata",):
            sys.exit(f"REFUSED: unexpected rsync destination {dst!r}")
    print(f"[safety] paths OK: src={src} dst={dst}", flush=True)
