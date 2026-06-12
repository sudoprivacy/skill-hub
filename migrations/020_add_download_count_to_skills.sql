-- Migration: Add download_count to skills table
-- Description: Track package downloads/installations per skill.

ALTER TABLE skills ADD COLUMN IF NOT EXISTS download_count INTEGER NOT NULL DEFAULT 0;

COMMENT ON COLUMN skills.download_count IS 'Number of package downloads/installations';

CREATE INDEX IF NOT EXISTS idx_skills_download_count ON skills(download_count DESC);
