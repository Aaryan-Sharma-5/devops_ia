"""StagePass — Event Registration & Operations (FastAPI + server-rendered Jinja2)."""
import re
import uuid
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from db import get_conn, query_all, query_one, db_health

app = FastAPI(title="StagePass")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def event_by_slug(slug: str):
    return query_one("SELECT * FROM events WHERE slug=%s", (slug,))


@app.get("/api/health")
def api_health():
    h = db_health()
    return {"app": "ok", "db": h}


@app.get("/api/events")
def api_events():
    return {"events": query_all("SELECT * FROM events ORDER BY event_date")}


@app.get("/api/events/{slug}/registrations")
def api_event_regs(slug: str):
    ev = event_by_slug(slug)
    if not ev:
        return JSONResponse({"error": "unknown event"}, status_code=404)
    rows = query_all(
        """SELECT b.id AS booking_id, b.tickets, b.simulation_batch_id, b.created_at,
                  a.name, a.email
           FROM bookings b JOIN attendees a ON a.id=b.attendee_id
           WHERE b.event_id=%s ORDER BY b.created_at DESC LIMIT 200""",
        (ev["id"],),
    )
    return {"event": ev["slug"], "count": len(rows), "registrations": rows}


@app.get("/api/registrations/recent")
def api_recent(limit: int = 10):
    limit = max(1, min(limit, 100))
    rows = query_all(
        """SELECT b.id AS booking_id, e.slug AS event_slug, e.title AS event_title,
                  a.name, a.email, b.tickets, b.simulation_batch_id, b.created_at
           FROM bookings b JOIN attendees a ON a.id=b.attendee_id
           JOIN events e ON e.id=b.event_id
           ORDER BY b.created_at DESC LIMIT %s""",
        (limit,),
    )
    return {"count": len(rows), "registrations": rows}


@app.get("/api/dashboard/summary")
def api_summary():
    total = query_one("SELECT COUNT(*) AS c FROM bookings")["c"]
    att = query_one("SELECT COUNT(*) AS c FROM attendees")["c"]
    per = query_all(
        """SELECT e.slug, e.title, COUNT(b.id) AS bookings, COALESCE(SUM(b.tickets),0) AS tickets
           FROM events e LEFT JOIN bookings b ON b.event_id=e.id
           GROUP BY e.slug, e.title, e.event_date ORDER BY e.event_date"""
    )
    garba = next((r for r in per if r["slug"] == "kjsce-garba-eve"), None)
    recent = query_all(
        """SELECT b.id AS booking_id, e.slug AS event_slug, a.name, a.email, b.tickets, b.created_at
           FROM bookings b JOIN attendees a ON a.id=b.attendee_id
           JOIN events e ON e.id=b.event_id
           ORDER BY b.created_at DESC LIMIT 10"""
    )
    return {
        "total_bookings": total,
        "total_attendees": att,
        "per_event": per,
        "garba_bookings": garba["bookings"] if garba else 0,
        "recent": recent,
        "db": db_health(),
    }


@app.post("/api/events/{slug}/register")
def api_register(slug: str, payload: dict):
    ev = event_by_slug(slug)
    if not ev:
        return JSONResponse({"error": "unknown event"}, status_code=404)
    name = str(payload.get("name", "")).strip()
    email = str(payload.get("email", "")).strip().lower()
    try:
        tickets = int(payload.get("tickets", 1))
    except (TypeError, ValueError):
        return JSONResponse({"error": "tickets must be an integer 1..10"}, status_code=400)
    batch = str(payload.get("simulation_batch_id") or "manual").strip()[:64]
    if len(name) < 2 or len(name) > 120:
        return JSONResponse({"error": "name must be 2..120 chars"}, status_code=400)
    if not EMAIL_RE.match(email) or len(email) > 200:
        return JSONResponse({"error": "invalid email"}, status_code=400)
    if not 1 <= tickets <= 10:
        return JSONResponse({"error": "tickets must be 1..10"}, status_code=400)
    booking_id = f"bk_{uuid.uuid4().hex[:12]}"
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO attendees(name,email) VALUES(%s,%s) "
                "ON CONFLICT(email) DO UPDATE SET name=EXCLUDED.name RETURNING id",
                (name, email),
            )
            attendee_id = cur.fetchone()[0]
            cur.execute(
                "INSERT INTO bookings(id,event_id,attendee_id,tickets,simulation_batch_id)"
                " VALUES(%s,%s,%s,%s,%s)",
                (booking_id, ev["id"], attendee_id, tickets, batch),
            )
        conn.commit()
    except Exception as e:  # noqa: BLE001
        conn.rollback()
        return JSONResponse({"error": f"db insert failed: {str(e)[:200]}"}, status_code=500)
    finally:
        conn.close()
    return {"booking_id": booking_id, "event": slug, "tickets": tickets}


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    events = query_all("SELECT * FROM events ORDER BY event_date")
    summary = api_summary()
    hero = next((e for e in events if e["slug"] == "kjsce-garba-eve"), events[0] if events else None)
    others = [e for e in events if hero and e["id"] != hero["id"]]
    return templates.TemplateResponse(
        "index.html", {"request": request, "hero": hero, "others": others, "summary": summary}
    )


@app.get("/admin", response_class=HTMLResponse)
def admin(request: Request):
    return ops(request)


@app.get("/ops", response_class=HTMLResponse)
def ops(request: Request):
    summary = api_summary()
    return templates.TemplateResponse("admin.html", {"request": request, "summary": summary})


@app.post("/register/{slug}", response_class=HTMLResponse)
async def register_form(request: Request, slug: str, name: str = Form(""), email: str = Form(""), tickets: int = Form(1)):
    result = api_register(slug, {"name": name, "email": email, "tickets": tickets})
    if isinstance(result, JSONResponse):
        msg, ok = result.body.decode(), False
    else:
        msg, ok = f"Registered! Booking ID: {result['booking_id']}", True
    events = query_all("SELECT * FROM events ORDER BY event_date")
    summary = api_summary()
    hero = next((e for e in events if e["slug"] == slug), None)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "hero": hero, "others": [e for e in events if e["slug"] != slug],
         "summary": summary, "flash": msg, "flash_ok": ok},
    )
