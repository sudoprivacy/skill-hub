-- Add core_features, applicable_scenarios, and sort_order to skills table
ALTER TABLE skills 
ADD COLUMN core_features TEXT,
ADD COLUMN applicable_scenarios TEXT,
ADD COLUMN sort_order INTEGER NOT NULL DEFAULT 0;
