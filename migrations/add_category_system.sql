-- Category System Migration
-- Adds category support to Agent Directory Exchange
-- Date: 2026-02-12

-- Add new columns to agents table
ALTER TABLE agents ADD COLUMN IF NOT EXISTS primary_use_case VARCHAR(100);
ALTER TABLE agents ADD COLUMN IF NOT EXISTS use_case_tags TEXT[];
ALTER TABLE agents ADD COLUMN IF NOT EXISTS skill_tags TEXT[];
ALTER TABLE agents ADD COLUMN IF NOT EXISTS industry_tags TEXT[];
ALTER TABLE agents ADD COLUMN IF NOT EXISTS slug VARCHAR(255) UNIQUE;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_agents_primary_use_case ON agents(primary_use_case);
CREATE INDEX IF NOT EXISTS idx_agents_use_case_tags ON agents USING GIN(use_case_tags);
CREATE INDEX IF NOT EXISTS idx_agents_slug ON agents(slug);

-- Create categories reference table
CREATE TABLE IF NOT EXISTS agent_categories (
    id SERIAL PRIMARY KEY,
    slug VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    search_volume INT DEFAULT 0,
    icon VARCHAR(100),
    parent_category VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Seed top 20 high-volume categories
INSERT INTO agent_categories (slug, name, description, search_volume, parent_category) VALUES
-- Content Creation (5 categories)
('agents-for-content-writing', 'Content Writing', 'AI agents specialized in creating written content for blogs, websites, and marketing materials', 10000, 'content'),
('agents-for-blog-writing', 'Blog Writing', 'AI agents for writing engaging blog posts and articles that drive traffic', 8000, 'content'),
('agents-for-social-media', 'Social Media Management', 'AI agents for creating and scheduling social media content across platforms', 9000, 'content'),
('agents-for-copywriting', 'Copywriting', 'AI agents for persuasive sales copy, ad copy, and marketing content', 7000, 'content'),
('agents-for-seo-content', 'SEO Content', 'AI agents for search-optimized content that ranks on Google', 6000, 'content'),

-- Customer Experience (3 categories)
('agents-for-customer-support', 'Customer Support', 'AI agents for handling customer inquiries, support tickets, and helpdesk', 12000, 'customer'),
('agents-for-live-chat', 'Live Chat', 'AI agents for real-time customer chat support and engagement', 8000, 'customer'),
('agents-for-email-support', 'Email Support', 'AI agents for managing customer email communications and responses', 6000, 'customer'),

-- Marketing & Sales (3 categories)
('agents-for-lead-generation', 'Lead Generation', 'AI agents for finding, qualifying, and nurturing sales leads', 11000, 'marketing'),
('agents-for-email-marketing', 'Email Marketing', 'AI agents for email campaign creation, automation, and optimization', 9000, 'marketing'),
('agents-for-sales-automation', 'Sales Automation', 'AI agents for automating sales workflows and outreach', 7000, 'marketing'),

-- Data & Research (3 categories)
('agents-for-data-analysis', 'Data Analysis', 'AI agents for analyzing, interpreting, and visualizing data', 10000, 'data'),
('agents-for-market-research', 'Market Research', 'AI agents for market analysis, competitive intelligence, and insights', 8000, 'data'),
('agents-for-web-scraping', 'Web Scraping', 'AI agents for extracting and processing data from websites', 7000, 'data'),

-- Development (3 categories)
('agents-for-coding', 'Coding & Development', 'AI agents for writing, reviewing, and optimizing code', 11000, 'development'),
('agents-for-testing', 'Software Testing', 'AI agents for automated testing, QA, and bug detection', 6000, 'development'),
('agents-for-debugging', 'Debugging', 'AI agents for finding and fixing code issues and errors', 5000, 'development'),

-- Operations (3 categories)
('agents-for-workflow-automation', 'Workflow Automation', 'AI agents for automating repetitive business processes', 9000, 'operations'),
('agents-for-task-management', 'Task Management', 'AI agents for organizing, prioritizing, and tracking tasks', 6000, 'operations'),
('agents-for-scheduling', 'Scheduling', 'AI agents for calendar management and appointment scheduling', 5000, 'operations')

ON CONFLICT (slug) DO NOTHING;

-- Create view for category page data
CREATE OR REPLACE VIEW category_with_counts AS
SELECT 
    ac.*,
    COUNT(a.id) as agent_count
FROM agent_categories ac
LEFT JOIN agents a ON a.primary_use_case = ac.slug
GROUP BY ac.id;

COMMENT ON TABLE agent_categories IS 'Categories for organizing agents by use case and search intent';
COMMENT ON COLUMN agents.primary_use_case IS 'Primary category slug (maps to agent_categories.slug)';
COMMENT ON COLUMN agents.use_case_tags IS 'Array of use case tags for multi-category listing';
COMMENT ON COLUMN agents.slug IS 'URL-friendly agent identifier (e.g., "a/xk9m")';
