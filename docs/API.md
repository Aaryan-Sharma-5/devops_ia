# StagePass API

Base URL (local): `http://localhost:8000`. All responses JSON unless noted.
Headline metric everywhere: **booking rows** (`COUNT(bookings)`).

## GET /api/health
Liveness + DB reachability.
```json
{"app": "ok", "db": {"status": "ok", "version": "PostgreSQL 17.11 ..."}}
```
`db.status` is `unavailable` (with truncated error) during restores; the app
retries connections instead of crashing.

## GET /api/events
All events ordered by date.
```json
{"events": [{"id":1,"slug":"kjsce-garba-eve","title":"KJSCE Garba Eve — 12 October",
"event_date":"2026-10-12","venue":"KJSCE Ground, Vidyavihar","timing":"7 PM onwards, 12 October",
"description":"...","ticket_info":"..."}, ...]}
```

## GET /api/events/{slug}/registrations
Registrations for one event (max 200, newest first).
`{event, count, registrations: [{booking_id, tickets, simulation_batch_id, created_at, name, email}]}`.
404 `{"error":"unknown event"}` for bad slugs.

## GET /api/registrations/recent?limit=10
Latest registrations across events (1..100, default 10).

## GET /api/dashboard/summary
Live ops snapshot — every number is a fresh SQL `COUNT`, never hardcoded:
`{total_bookings, total_attendees, per_event: [{slug,title,bookings,tickets}],
garba_bookings, recent: [...10], db: {...}}`.

## POST /api/events/{slug}/register
Body: `{"name": "...", "email": "a@b.test", "tickets": 1, "simulation_batch_id": "batch"}`.
Validation: name 2–120 chars; email regex + ≤200 chars; tickets int 1–10.
Inserts attendee (upsert on email) + booking in ONE transaction.
200: `{"booking_id": "bk_<12hex>", "event": slug, "tickets": n}`.
400 on validation failure; 404 on unknown event; 500 (rolled back) on DB errors.

## Pages (server-rendered)
- `GET /` — hero for KJSCE Garba Eve (12 OCT badge), registration form, live snapshot, other events.
- `GET /admin` (alias `/ops`) — operations dashboard from `/api/dashboard/summary`.
- `POST /register/{slug}` — HTML form handler, same validation, shows success/error + booking ID.
