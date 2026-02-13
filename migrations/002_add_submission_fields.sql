-- Migration: Add fields for public agent submissions
-- Date: 2026-02-13
-- Description: Adds columns to support public submission workflow with manual review

-- Add submission and review fields to agents table
ALTER TABLE agents
ADD COLUMN IF NOT EXISTS pending_review BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS submission_source VARCHAR(100),
ADD COLUMN IF NOT EXISTS auto_discovered BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS rejected_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS rejection_reason TEXT,
ADD COLUMN IF NOT EXISTS verified BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS source_url VARCHAR(500),
ADD COLUMN IF NOT EXISTS categories JSONB;

-- Add indexes for common queries
CREATE INDEX IF NOT EXISTS idx_agents_pending_review ON agents(pending_review) WHERE pending_review = TRUE;
CREATE INDEX IF NOT EXISTS idx_agents_submission_source ON agents(submission_source);
CREATE INDEX IF NOT EXISTS idx_agents_source_url ON agents(source_url);

-- Add comment
COMMENT ON COLUMN agents.pending_review IS 'Indicates agent is awaiting manual review/approval';
COMMENT ON COLUMN agents.submission_source IS 'Source of submission: web_form, crawler, api';
COMMENT ON COLUMN agents.auto_discovered IS 'TRUE if discovered by crawler, FALSE if manually submitted';
COMMENT ON COLUMN agents.source_url IS 'Original source URL (GitHub, HuggingFace, website)';
COMMENT ON COLUMN agents.categories IS 'JSON array of category tags';
