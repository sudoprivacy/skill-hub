-- Add status to skills table

ALTER TABLE skills
ADD COLUMN status INTEGER NOT NULL DEFAULT 0;

COMMENT ON COLUMN skills.status IS 'Skill status (0: default/active, other values for specific states)';
