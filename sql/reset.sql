-- Clean reset of demo data (keeps events, clears bookings/attendees + benchmark table).
TRUNCATE bookings, attendees RESTART IDENTITY CASCADE;
DROP TABLE IF EXISTS bench_payload;
