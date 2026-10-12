-- Verification queries used by scenarios/tests.
SELECT (SELECT COUNT(*) FROM bookings) AS total_bookings,
       (SELECT COUNT(*) FROM bookings b JOIN events e ON e.id=b.event_id WHERE e.slug='kjsce-garba-eve') AS garba_bookings,
       (SELECT COUNT(*) FROM bookings b JOIN events e ON e.id=b.event_id WHERE e.slug='maker-weekend') AS maker_bookings,
       (SELECT COUNT(*) FROM bookings b JOIN events e ON e.id=b.event_id WHERE e.slug='open-air-cinema') AS cinema_bookings;
-- FK integrity + orphan check:
SELECT COUNT(*) AS orphan_bookings FROM bookings b LEFT JOIN events e ON e.id=b.event_id WHERE e.id IS NULL;
SELECT COUNT(*) AS orphan_attendees FROM bookings b LEFT JOIN attendees a ON a.id=b.attendee_id WHERE a.id IS NULL;
