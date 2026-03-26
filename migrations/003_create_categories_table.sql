-- Create Categories Table
CREATE TABLE IF NOT EXISTS categories (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    display_name VARCHAR(255) NOT NULL,
    order_index INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS ix_categories_name ON categories(name);
CREATE INDEX IF NOT EXISTS ix_categories_created_at ON categories(created_at);

-- Add comment to table and columns
COMMENT ON TABLE categories IS 'Categories table representing skill categories';
COMMENT ON COLUMN categories.id IS 'Unique identifier for the category';
COMMENT ON COLUMN categories.name IS 'Category code/identifier';
COMMENT ON COLUMN categories.display_name IS 'Display name';
COMMENT ON COLUMN categories.order_index IS 'Ordering index for display';
COMMENT ON COLUMN categories.created_at IS 'Creation time';
COMMENT ON COLUMN categories.updated_at IS 'Last update time';
