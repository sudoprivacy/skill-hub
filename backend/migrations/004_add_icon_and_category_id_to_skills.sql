-- Add category_id and icon to skills table
ALTER TABLE skills 
ADD COLUMN IF NOT EXISTS category_id UUID REFERENCES categories(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS icon VARCHAR(200);

-- Create index for category_id
CREATE INDEX IF NOT EXISTS ix_skills_category_id ON skills(category_id);

-- Add comments
COMMENT ON COLUMN skills.category_id IS 'Foreign key to categories table';
COMMENT ON COLUMN skills.icon IS 'Icon URL or path';
