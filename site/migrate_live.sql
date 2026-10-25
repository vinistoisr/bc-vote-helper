-- Frozen totals for the live party split on /results/: one row per completed block of 25 people, written once.
-- Later edits to answers already counted never change a published block.
CREATE TABLE IF NOT EXISTS live_blocks (
  block INTEGER PRIMARY KEY,
  totals TEXT NOT NULL,
  created_at TEXT NOT NULL
);
