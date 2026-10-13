-- Languages: the page language of each session. Run once against the V2 database before deploying the
-- multi-language page and Worker (the Worker's insert names this column and fails without it).
-- A database created from the current schema.sql already has the column; skip this file there.
-- Older rows keep lang = NULL and show as "Not given" in the dashboard.
ALTER TABLE submissions ADD COLUMN lang TEXT;
