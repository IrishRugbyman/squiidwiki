-- Add timestamp columns to alliances table
ALTER TABLE alliances 
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE;

-- Update existing rows to have a created_at timestamp
UPDATE alliances SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL; 