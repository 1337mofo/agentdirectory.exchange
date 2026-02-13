-- Fix schema: Add missing source_url column to agents table
-- Run this in Railway PostgreSQL console

ALTER TABLE agents ADD COLUMN IF NOT EXISTS source_url TEXT;

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_agents_source_url ON agents(source_url);

-- Verify the column exists
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'agents' 
ORDER BY ordinal_position;
