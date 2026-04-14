-- Migration: Add source_url to assistants table
-- Description: Add source_url column to store uploaded zip file path

ALTER TABLE assistants ADD COLUMN IF NOT EXISTS source_url VARCHAR(500);

COMMENT ON COLUMN assistants.source_url IS 'Path or URL to the uploaded zip file containing the assistant logic';
