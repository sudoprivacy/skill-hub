-- Migration: Create skill_versions table
-- Description: Stores version information for skills

CREATE TABLE IF NOT EXISTS skill_versions (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Foreign key to skills table
    skill_id UUID NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
    
    -- Version information
    version VARCHAR(50) NOT NULL,
    source_url TEXT NOT NULL,
    checksum VARCHAR(64) NOT NULL, -- SHA-256 hash (64 characters)
    changelog TEXT,
    readme_content TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT unique_skill_version UNIQUE(skill_id, version),
    CONSTRAINT valid_version_format CHECK (version ~ '^v?\d+(\.\d+){0,2}(-[a-zA-Z0-9\.]+)?$')
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_skill_versions_skill_id ON skill_versions(skill_id);
CREATE INDEX IF NOT EXISTS idx_skill_versions_version ON skill_versions(version);
CREATE INDEX IF NOT EXISTS idx_skill_versions_created_at ON skill_versions(created_at);

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_skill_versions_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_skill_versions_updated_at
    BEFORE UPDATE ON skill_versions
    FOR EACH ROW
    EXECUTE FUNCTION update_skill_versions_updated_at();

-- Add comment to table
COMMENT ON TABLE skill_versions IS 'Stores version information for skills, including source URLs, checksums, and documentation';

-- Add comments to columns
COMMENT ON COLUMN skill_versions.id IS 'Unique identifier for the version';
COMMENT ON COLUMN skill_versions.skill_id IS 'Foreign key referencing the parent skill';
COMMENT ON COLUMN skill_versions.version IS 'Semantic version (e.g., v1.2.0)';
COMMENT ON COLUMN skill_versions.source_url IS 'URL to download the compressed package or Git repository';
COMMENT ON COLUMN skill_versions.checksum IS 'SHA-256 hash of the file for security verification';
COMMENT ON COLUMN skill_versions.changelog IS 'Description of changes in this version';
COMMENT ON COLUMN skill_versions.readme_content IS 'Full content of SKILL.md for display in details';
COMMENT ON COLUMN skill_versions.created_at IS 'Timestamp when the version was created';
COMMENT ON COLUMN skill_versions.updated_at IS 'Timestamp when the version was last updated';