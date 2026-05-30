-- Migration: Create assistants table
-- Description: Create the assistants table to store digital assistants (数字助手)

CREATE TABLE IF NOT EXISTS assistants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    profession VARCHAR(255) NOT NULL,
    description TEXT,
    prompt_file VARCHAR(500),
    avatar VARCHAR(500),
    default_init_prompt TEXT,
    category_id UUID REFERENCES categories(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_assistants_name ON assistants(name);
CREATE INDEX IF NOT EXISTS idx_assistants_category_id ON assistants(category_id);
CREATE INDEX IF NOT EXISTS idx_assistants_created_at ON assistants(created_at DESC);

-- Trigger for updated_at
CREATE TRIGGER update_assistants_updated_at 
    BEFORE UPDATE ON assistants 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Comments
COMMENT ON TABLE assistants IS 'Assistant entities (数字助手)';
COMMENT ON COLUMN assistants.id IS 'Unique identifier';
COMMENT ON COLUMN assistants.name IS 'Assistant name';
COMMENT ON COLUMN assistants.profession IS 'Assistant profession/role';
COMMENT ON COLUMN assistants.description IS 'Assistant description';
COMMENT ON COLUMN assistants.prompt_file IS 'Path or URL to the markdown prompt file';
COMMENT ON COLUMN assistants.avatar IS 'URL to the assistant avatar image';
COMMENT ON COLUMN assistants.default_init_prompt IS 'Default initial prompt text';
COMMENT ON COLUMN assistants.category_id IS 'Reference to the category (must be type 1)';
