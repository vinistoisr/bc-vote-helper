-- BC Vote Helper 2026 anonymous responses. No names, no IP addresses.
CREATE TABLE IF NOT EXISTS submissions (
  sid TEXT PRIMARY KEY,          -- random id made in the browser, one per quiz session (1-4 people)
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,      -- changes when people edit answers and finish again
  count INTEGER NOT NULL,
  country TEXT,
  region TEXT,
  region_code TEXT,
  city TEXT,
  data_as_of TEXT,               -- spec version the answers were given against
  riding TEXT                    -- 3-letter riding code (V2), NULL when not given; never a postal code
);
CREATE INDEX IF NOT EXISTS submissions_created ON submissions (created_at);
CREATE INDEX IF NOT EXISTS submissions_riding ON submissions (riding);

CREATE TABLE IF NOT EXISTS people (
  sid TEXT NOT NULL,
  idx INTEGER NOT NULL,
  level INTEGER NOT NULL,        -- reading level 1-5
  answered INTEGER NOT NULL,
  answers TEXT NOT NULL,         -- JSON {question_id: {c: option id or "skip", w: low|medium|high}}
  PRIMARY KEY (sid, idx)
);
