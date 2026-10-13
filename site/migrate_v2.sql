-- V2: one riding per session. Run once against a V1-era database, then schema.sql is current.
-- Old rows keep riding = NULL and show as "Not given" in the dashboard.
ALTER TABLE submissions ADD COLUMN riding TEXT;
CREATE INDEX IF NOT EXISTS submissions_riding ON submissions (riding);
