-- Migration: Add sort_order to assistants table
-- Description: Add sort_order column to support custom sorting

ALTER TABLE assistants ADD COLUMN IF NOT EXISTS sort_order INTEGER NOT NULL DEFAULT 0;

COMMENT ON COLUMN assistants.sort_order IS 'Sort order for display priority';
