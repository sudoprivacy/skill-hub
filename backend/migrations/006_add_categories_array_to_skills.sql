-- Add categories array to skills table
ALTER TABLE skills 
ADD COLUMN categories VARCHAR[];
