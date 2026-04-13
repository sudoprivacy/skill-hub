-- Add type to categories table
ALTER TABLE categories ADD COLUMN type INTEGER NOT NULL DEFAULT 0;
COMMENT ON COLUMN categories.type IS '0 for skill, 1 for assistant';
