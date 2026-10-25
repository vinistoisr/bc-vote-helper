-- Traffic source on shared sessions, plus a plain counter of finished quizzes (including people who did not share).
-- Run once against each database BEFORE deploying the Worker that writes these (its insert names the column).
-- completions holds no answers, no session id, no location: only when, language, source category and number of people.
ALTER TABLE submissions ADD COLUMN source TEXT;
CREATE TABLE IF NOT EXISTS completions (
  created_at TEXT NOT NULL,
  lang TEXT,
  source TEXT,
  count INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS completions_created ON completions (created_at);
