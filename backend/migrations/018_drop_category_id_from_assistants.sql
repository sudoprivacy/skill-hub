-- Remove category_id from assistants table
ALTER TABLE assistants DROP COLUMN IF EXISTS category_id;
