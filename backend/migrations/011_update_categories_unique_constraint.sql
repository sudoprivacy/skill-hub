-- Migration: Update categories unique constraint
-- Description: Drop the global unique constraint on `name` and add a composite unique constraint on `(name, type)`

-- Step 1: Drop the existing unique constraint on the `name` column
-- In PostgreSQL, if the unique constraint was created via the UNIQUE keyword on column definition, 
-- its default name is usually `<table_name>_<column_name>_key`.
-- For SQLite, altering constraints is more complex, but we'll assume a standard PostgreSQL/MySQL approach for now, 
-- or use standard ALTER TABLE DROP CONSTRAINT.
ALTER TABLE categories DROP CONSTRAINT IF EXISTS categories_name_key;

-- Step 2: Add the new composite unique constraint on `(name, type)`
ALTER TABLE categories ADD CONSTRAINT uix_category_name_type UNIQUE (name, type);
