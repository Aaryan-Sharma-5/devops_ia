-- CONTROLLED INCIDENT (lab only): delete all KJSCE Garba Eve bookings. Guarded by scripts.
-- Resolves event id by slug; reports affected rows.
WITH ev AS (SELECT id FROM events WHERE slug='kjsce-garba-eve')
DELETE FROM bookings USING ev WHERE bookings.event_id=ev.id;
SELECT count(*) AS garba_remaining FROM bookings b JOIN events e ON e.id=b.event_id WHERE e.slug='kjsce-garba-eve';
SELECT count(*) AS total_remaining FROM bookings;
