-- Add status field to assistants table
ALTER TABLE assistants ADD COLUMN status INTEGER DEFAULT 0 NOT NULL;
COMMENT ON COLUMN assistants.status IS 'Assistant status (0: pending review, 1: active/approved, other values for specific states)';
