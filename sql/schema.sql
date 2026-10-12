-- StagePass schema (idempotent). Headline metric = COUNT(bookings) rows.
CREATE TABLE IF NOT EXISTS events(
  id SERIAL PRIMARY KEY,
  slug TEXT UNIQUE NOT NULL,
  title TEXT NOT NULL,
  event_date DATE NOT NULL,
  venue TEXT NOT NULL,
  timing TEXT NOT NULL,
  description TEXT NOT NULL,
  ticket_info TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS attendees(
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL CHECK (char_length(name) BETWEEN 2 AND 120),
  email TEXT UNIQUE NOT NULL
);
CREATE TABLE IF NOT EXISTS bookings(
  id TEXT PRIMARY KEY,
  event_id INT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
  attendee_id INT NOT NULL REFERENCES attendees(id) ON DELETE RESTRICT,
  tickets INT NOT NULL CHECK (tickets BETWEEN 1 AND 10),
  simulation_batch_id TEXT NOT NULL DEFAULT 'seed',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_bookings_event ON bookings(event_id);
CREATE INDEX IF NOT EXISTS idx_bookings_batch ON bookings(simulation_batch_id);
CREATE INDEX IF NOT EXISTS idx_bookings_created ON bookings(created_at);
