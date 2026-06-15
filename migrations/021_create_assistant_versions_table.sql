-- Migration: Create assistant_versions table
-- Description: Stores version information and uploaded ZIP source paths for assistants.

CREATE TABLE IF NOT EXISTS assistant_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assistant_id UUID NOT NULL REFERENCES assistants(id) ON DELETE CASCADE,
    version VARCHAR(50) NOT NULL,
    source_url TEXT NOT NULL,
    checksum VARCHAR(64) NOT NULL DEFAULT '',
    changelog TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_assistant_version UNIQUE(assistant_id, version),
    CONSTRAINT valid_assistant_version_format CHECK (version ~ '^v?\d+(\.\d+){0,2}(-[a-zA-Z0-9\.]+)?$')
);

CREATE INDEX IF NOT EXISTS idx_assistant_versions_assistant_id ON assistant_versions(assistant_id);
CREATE INDEX IF NOT EXISTS idx_assistant_versions_version ON assistant_versions(version);
CREATE INDEX IF NOT EXISTS idx_assistant_versions_created_at ON assistant_versions(created_at);

CREATE OR REPLACE FUNCTION update_assistant_versions_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_assistant_versions_updated_at ON assistant_versions;
CREATE TRIGGER trigger_update_assistant_versions_updated_at
    BEFORE UPDATE ON assistant_versions
    FOR EACH ROW
    EXECUTE FUNCTION update_assistant_versions_updated_at();

INSERT INTO assistant_versions (
    assistant_id,
    version,
    source_url,
    checksum,
    changelog,
    created_at,
    updated_at
)
SELECT
    id,
    'v1.0.0',
    source_url,
    '',
    'Migrated from assistants.source_url',
    created_at,
    updated_at
FROM assistants
WHERE source_url IS NOT NULL
  AND source_url <> ''
ON CONFLICT (assistant_id, version) DO NOTHING;

COMMENT ON TABLE assistant_versions IS 'Stores version information for assistants, including source ZIP paths';
COMMENT ON COLUMN assistant_versions.id IS 'Unique identifier for the version';
COMMENT ON COLUMN assistant_versions.assistant_id IS 'Foreign key referencing the parent assistant';
COMMENT ON COLUMN assistant_versions.version IS 'Semantic version (e.g., v1.2.0)';
COMMENT ON COLUMN assistant_versions.source_url IS 'Path or URL to the uploaded assistant ZIP package';
COMMENT ON COLUMN assistant_versions.checksum IS 'SHA-256 hash of the file for security verification';
COMMENT ON COLUMN assistant_versions.changelog IS 'Description of changes in this version';
COMMENT ON COLUMN assistant_versions.created_at IS 'Timestamp when the version was created';
COMMENT ON COLUMN assistant_versions.updated_at IS 'Timestamp when the version was last updated';
