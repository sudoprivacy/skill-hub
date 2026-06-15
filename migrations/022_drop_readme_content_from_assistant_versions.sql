-- Migration: Drop readme_content from assistant_versions
-- Description: Assistant version records only store ZIP package path and version metadata.

ALTER TABLE assistant_versions DROP COLUMN IF EXISTS readme_content;
