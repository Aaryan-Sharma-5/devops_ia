-- Deterministic seed: 100 bookings (20 Garba / 50 Maker / 30 Cinema). Rerunnable, no duplicates.
-- Configurable Garba date via GARBA_DATE (default 2026-10-12).
INSERT INTO events(slug,title,event_date,venue,timing,description,ticket_info) VALUES
 ('kjsce-garba-eve','KJSCE Garba Eve — 12 October',COALESCE(NULLIF(current_setting('stagepass.garba_date', true),''),'2026-10-12')::date,
  'KJSCE Ground, Vidyavihar','7 PM onwards, 12 October',
  'A festive Navratri Garba night with live dhol, traditional décor and food stalls. Flagship StagePass event.',
  'General entry · group passes available'),
 ('maker-weekend','Maker Weekend','2026-10-18',
  'Innovation Lab, KJSCE','10 AM – 6 PM',
  'Hands-on build weekend: 3D printing, robotics demos and student showcases.',
  'Day pass · team tickets'),
 ('open-air-cinema','Open-Air Cinema','2026-10-25',
  'Central Lawns, KJSCE','7:30 PM onwards',
  'Classic films under the stars with bean bags, popcorn and food trucks.',
  'Lawn seating · premium recliners')
ON CONFLICT(slug) DO UPDATE SET title=EXCLUDED.title, event_date=EXCLUDED.event_date,
  venue=EXCLUDED.venue, timing=EXCLUDED.timing, description=EXCLUDED.description, ticket_info=EXCLUDED.ticket_info;

-- Step 1: deterministic attendees (separate statement so later joins see them).
INSERT INTO attendees(name,email)
SELECT 'Seed Attendee '||g, 'seed'||lpad(g::text,3,'0')||'@example.test'
FROM generate_series(1,100) g
ON CONFLICT(email) DO NOTHING;

-- Step 2: deterministic bookings bk_seed_001..100 (20 Garba / 50 Maker / 30 Cinema).
INSERT INTO bookings(id,event_id,attendee_id,tickets,simulation_batch_id)
SELECT 'bk_seed_'||lpad(g::text,3,'0'), e.id, a.id, 1+((g*7)%4), 'seed'
FROM generate_series(1,100) g
JOIN LATERAL (SELECT CASE WHEN g<=20 THEN 'kjsce-garba-eve' WHEN g<=70 THEN 'maker-weekend'
                          ELSE 'open-air-cinema' END AS slug) s ON true
JOIN events e ON e.slug=s.slug
JOIN attendees a ON a.email='seed'||lpad(g::text,3,'0')||'@example.test'
ON CONFLICT(id) DO NOTHING;
