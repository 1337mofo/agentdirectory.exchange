-- 100 Category System Migration
-- Agent Directory Exchange - Top 100 Google Search Terms
-- Date: 2026-02-12

-- Add new columns to agents table (if not already added)
ALTER TABLE agents ADD COLUMN IF NOT EXISTS primary_use_case VARCHAR(100);
ALTER TABLE agents ADD COLUMN IF NOT EXISTS use_case_tags TEXT[];
ALTER TABLE agents ADD COLUMN IF NOT EXISTS skill_tags TEXT[];
ALTER TABLE agents ADD COLUMN IF NOT EXISTS industry_tags TEXT[];
ALTER TABLE agents ADD COLUMN IF NOT EXISTS slug VARCHAR(255) UNIQUE;
ALTER TABLE agents ADD COLUMN IF NOT EXISTS protocol_support JSONB DEFAULT '{}';
ALTER TABLE agents ADD COLUMN IF NOT EXISTS agntcy_member BOOLEAN DEFAULT FALSE;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_agents_primary_use_case ON agents(primary_use_case);
CREATE INDEX IF NOT EXISTS idx_agents_use_case_tags ON agents USING GIN(use_case_tags);
CREATE INDEX IF NOT EXISTS idx_agents_slug ON agents(slug);
CREATE INDEX IF NOT EXISTS idx_agents_protocol_support ON agents USING GIN(protocol_support);

-- Create categories reference table
CREATE TABLE IF NOT EXISTS agent_categories (
    id SERIAL PRIMARY KEY,
    slug VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    search_volume INT DEFAULT 0,
    tier INT DEFAULT 4,  -- 1=ultra high, 2=high, 3=medium, 4=niche
    icon VARCHAR(100),
    parent_category VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Seed TOP 100 categories (organized by tier)

-- TIER 1: Ultra High-Volume (10,000+ searches/month) - Deploy Week 1
INSERT INTO agent_categories (slug, name, description, search_volume, tier, parent_category) VALUES
('agents-for-customer-support', 'Customer Support', 'AI agents for handling customer inquiries, support tickets, and helpdesk operations', 12000, 1, 'customer'),
('agents-for-coding', 'Coding & Development', 'AI agents for writing, reviewing, and optimizing code across multiple programming languages', 11000, 1, 'development'),
('agents-for-lead-generation', 'Lead Generation', 'AI agents for finding, qualifying, and nurturing sales leads', 11000, 1, 'marketing'),
('agents-for-content-writing', 'Content Writing', 'AI agents specialized in creating written content for blogs, websites, and marketing', 10000, 1, 'content'),
('agents-for-customer-service', 'Customer Service', 'AI agents for providing customer service and support across channels', 10000, 1, 'customer'),
('agents-for-data-analysis', 'Data Analysis', 'AI agents for analyzing, interpreting, and visualizing data', 10000, 1, 'data'),
('agents-for-workflow-automation', 'Workflow Automation', 'AI agents for automating repetitive business processes and workflows', 9000, 1, 'operations'),
('agents-for-social-media-posts', 'Social Media Posts', 'AI agents for creating and scheduling social media content', 9000, 1, 'content'),
('agents-for-email-marketing', 'Email Marketing', 'AI agents for email campaign creation, automation, and optimization', 9000, 1, 'marketing'),
('agents-for-blog-writing', 'Blog Writing', 'AI agents for writing engaging blog posts and articles', 8000, 1, 'content'),
('agents-for-live-chat', 'Live Chat Support', 'AI agents for real-time customer chat support', 8000, 1, 'customer'),
('agents-for-market-research', 'Market Research', 'AI agents for market analysis, competitive intelligence, and insights', 8000, 1, 'data'),
('agents-for-copywriting', 'Copywriting', 'AI agents for persuasive sales copy, ad copy, and marketing content', 7000, 1, 'content'),
('agents-for-sales-automation', 'Sales Automation', 'AI agents for automating sales workflows and outreach', 7000, 1, 'marketing'),
('agents-for-web-scraping', 'Web Scraping', 'AI agents for extracting and processing data from websites', 7000, 1, 'data'),
('agents-for-chatbot', 'Chatbot', 'AI agents for conversational interfaces and automated chat', 7000, 1, 'customer'),
('agents-for-virtual-assistant', 'Virtual Assistant', 'AI agents for personal and business virtual assistance', 6500, 1, 'operations'),
('agents-for-marketing-automation', 'Marketing Automation', 'AI agents for automating marketing campaigns and workflows', 6500, 1, 'marketing'),
('agents-for-seo-content', 'SEO Content', 'AI agents for search-optimized content that ranks on Google', 6000, 1, 'content'),
('agents-for-email-support', 'Email Support', 'AI agents for managing customer email communications', 6000, 1, 'customer')
ON CONFLICT (slug) DO NOTHING;

-- TIER 2: High-Volume (3,000-5,999 searches/month) - Deploy Week 2
INSERT INTO agent_categories (slug, name, description, search_volume, tier, parent_category) VALUES
('agents-for-research', 'Research', 'AI agents for conducting research and gathering information', 6000, 2, 'data'),
('agents-for-testing', 'Software Testing', 'AI agents for automated testing and QA', 6000, 2, 'development'),
('agents-for-task-management', 'Task Management', 'AI agents for organizing and tracking tasks', 6000, 2, 'operations'),
('agents-for-image-generation', 'Image Generation', 'AI agents for creating and generating images', 6000, 2, 'creative'),
('agents-for-competitive-analysis', 'Competitive Analysis', 'AI agents for analyzing competitors and market positioning', 5500, 2, 'data'),
('agents-for-helpdesk', 'Helpdesk Automation', 'AI agents for helpdesk ticket management and resolution', 5000, 2, 'customer'),
('agents-for-social-media-marketing', 'Social Media Marketing', 'AI agents for social media marketing campaigns', 5000, 2, 'marketing'),
('agents-for-debugging', 'Debugging', 'AI agents for finding and fixing code issues', 5000, 2, 'development'),
('agents-for-scheduling', 'Scheduling', 'AI agents for calendar and appointment management', 5000, 2, 'operations'),
('agents-for-email-copywriting', 'Email Copywriting', 'AI agents for writing marketing and sales emails', 5000, 2, 'content'),
('agents-for-graphic-design', 'Graphic Design', 'AI agents for creating visual designs and graphics', 5000, 2, 'creative'),
('agents-for-project-management', 'Project Management', 'AI agents for managing projects and teams', 4500, 2, 'operations'),
('agents-for-cold-outreach', 'Cold Outreach', 'AI agents for sales prospecting and cold outreach', 4500, 2, 'marketing'),
('agents-for-product-descriptions', 'Product Descriptions', 'AI agents for writing product descriptions and listings', 4500, 2, 'content'),
('agents-for-video-editing', 'Video Editing', 'AI agents for editing and producing videos', 4500, 2, 'creative'),
('agents-for-ad-copy', 'Ad Copy', 'AI agents for creating advertising copy', 4500, 2, 'content'),
('agents-for-data-entry', 'Data Entry', 'AI agents for automated data entry and processing', 4000, 2, 'data'),
('agents-for-video-scripts', 'Video Scripts', 'AI agents for writing video scripts and storyboards', 4000, 2, 'content'),
('agents-for-python-coding', 'Python Coding', 'AI agents specialized in Python programming', 4000, 2, 'development'),
('agents-for-financial-analysis', 'Financial Analysis', 'AI agents for analyzing financial data and metrics', 4000, 2, 'finance'),
('agents-for-linkedin-posts', 'LinkedIn Posts', 'AI agents for creating LinkedIn content', 3500, 2, 'content'),
('agents-for-linkedin-outreach', 'LinkedIn Outreach', 'AI agents for LinkedIn prospecting and outreach', 3500, 2, 'marketing'),
('agents-for-email-campaigns', 'Email Campaigns', 'AI agents for managing email marketing campaigns', 3500, 2, 'marketing'),
('agents-for-meeting-notes', 'Meeting Notes', 'AI agents for taking and summarizing meeting notes', 3500, 2, 'operations'),
('agents-for-photo-editing', 'Photo Editing', 'AI agents for editing and enhancing photos', 3500, 2, 'creative'),
('agents-for-email-management', 'Email Management', 'AI agents for organizing and managing email', 3500, 2, 'operations'),
('agents-for-technical-writing', 'Technical Writing', 'AI agents for technical documentation and writing', 3500, 2, 'content'),
('agents-for-javascript-coding', 'JavaScript Coding', 'AI agents specialized in JavaScript development', 3500, 2, 'development'),
('agents-for-code-review', 'Code Review', 'AI agents for reviewing and auditing code', 3500, 2, 'development'),
('agents-for-bookkeeping', 'Bookkeeping', 'AI agents for bookkeeping and financial record keeping', 3500, 2, 'finance')
ON CONFLICT (slug) DO NOTHING;

-- TIER 3: Medium-Volume (1,500-2,999 searches/month) - Deploy Week 3
INSERT INTO agent_categories (slug, name, description, search_volume, tier, parent_category) VALUES
('agents-for-instagram-captions', 'Instagram Captions', 'AI agents for writing Instagram captions', 3000, 3, 'content'),
('agents-for-ghostwriting', 'Ghostwriting', 'AI agents for ghostwriting books, articles, and content', 3000, 3, 'content'),
('agents-for-documentation', 'Documentation', 'AI agents for creating technical and product documentation', 3000, 3, 'development'),
('agents-for-sql-queries', 'SQL Queries', 'AI agents for writing and optimizing SQL queries', 3000, 3, 'development'),
('agents-for-crm-automation', 'CRM Automation', 'AI agents for automating CRM workflows', 3000, 3, 'marketing'),
('agents-for-calendar-management', 'Calendar Management', 'AI agents for managing calendars and appointments', 3000, 3, 'operations'),
('agents-for-data-visualization', 'Data Visualization', 'AI agents for creating charts and visual data representations', 3000, 3, 'data'),
('agents-for-accounting', 'Accounting', 'AI agents for accounting and financial management', 3000, 3, 'finance'),
('agents-for-logo-design', 'Logo Design', 'AI agents for creating logos and brand identities', 3000, 3, 'creative'),
('agents-for-lead-qualification', 'Lead Qualification', 'AI agents for qualifying and scoring sales leads', 2800, 3, 'marketing'),
('agents-for-trend-analysis', 'Trend Analysis', 'AI agents for identifying and analyzing trends', 2800, 3, 'data'),
('agents-for-twitter-threads', 'Twitter Threads', 'AI agents for creating Twitter thread content', 2500, 3, 'content'),
('agents-for-sentiment-analysis', 'Sentiment Analysis', 'AI agents for analyzing sentiment in text and social media', 2500, 3, 'data'),
('agents-for-api-integration', 'API Integration', 'AI agents for integrating APIs and systems', 2500, 3, 'development'),
('agents-for-bug-fixing', 'Bug Fixing', 'AI agents for identifying and fixing software bugs', 2500, 3, 'development'),
('agents-for-ui-design', 'UI Design', 'AI agents for user interface design', 2500, 3, 'creative'),
('agents-for-document-processing', 'Document Processing', 'AI agents for processing and extracting data from documents', 2500, 3, 'operations'),
('agents-for-tax-preparation', 'Tax Preparation', 'AI agents for tax filing and preparation', 2500, 3, 'finance'),
('agents-for-forecasting', 'Forecasting', 'AI agents for financial and business forecasting', 2500, 3, 'finance'),
('agents-for-affiliate-marketing', 'Affiliate Marketing', 'AI agents for affiliate marketing campaigns', 2500, 3, 'marketing'),
('agents-for-faq-automation', 'FAQ Automation', 'AI agents for automating FAQ responses', 2500, 3, 'customer'),
('agents-for-sales-calls', 'Sales Calls', 'AI agents for conducting and managing sales calls', 2500, 3, 'marketing'),
('agents-for-follow-up-emails', 'Follow-up Emails', 'AI agents for automated follow-up email sequences', 2200, 3, 'marketing'),
('agents-for-business-intelligence', 'Business Intelligence', 'AI agents for BI analysis and reporting', 3500, 3, 'data'),
('agents-for-press-releases', 'Press Releases', 'AI agents for writing press releases and media content', 2000, 3, 'content'),
('agents-for-price-monitoring', 'Price Monitoring', 'AI agents for tracking competitor pricing', 2000, 3, 'data'),
('agents-for-survey-analysis', 'Survey Analysis', 'AI agents for analyzing survey data and feedback', 2000, 3, 'data'),
('agents-for-devops', 'DevOps', 'AI agents for DevOps automation and infrastructure', 2000, 3, 'development'),
('agents-for-invoice-processing', 'Invoice Processing', 'AI agents for processing and managing invoices', 2000, 3, 'operations'),
('agents-for-phone-support', 'Phone Support', 'AI agents for automated phone support', 2000, 3, 'customer')
ON CONFLICT (slug) DO NOTHING;

-- TIER 4: Niche-Volume (1,000-1,499 searches/month) - Deploy Week 4
INSERT INTO agent_categories (slug, name, description, search_volume, tier, parent_category) VALUES
('agents-for-presentation-design', 'Presentation Design', 'AI agents for creating presentations and slide decks', 2000, 4, 'creative'),
('agents-for-influencer-outreach', 'Influencer Outreach', 'AI agents for reaching out to influencers', 2000, 4, 'marketing'),
('agents-for-budget-planning', 'Budget Planning', 'AI agents for financial budget planning', 2000, 4, 'finance'),
('agents-for-risk-analysis', 'Risk Analysis', 'AI agents for analyzing business and financial risk', 2000, 4, 'finance'),
('agents-for-drip-campaigns', 'Drip Campaigns', 'AI agents for automated drip email campaigns', 1800, 4, 'marketing'),
('agents-for-multilingual-support', 'Multilingual Support', 'AI agents for customer support in multiple languages', 1800, 4, 'customer'),
('agents-for-unit-testing', 'Unit Testing', 'AI agents for automated unit testing', 1800, 4, 'development'),
('agents-for-expense-tracking', 'Expense Tracking', 'AI agents for tracking business expenses', 1800, 4, 'finance'),
('agents-for-fraud-detection', 'Fraud Detection', 'AI agents for detecting fraudulent activity', 1800, 4, 'finance'),
('agents-for-payroll', 'Payroll', 'AI agents for payroll processing and management', 1800, 4, 'finance'),
('agents-for-infographic-creation', 'Infographic Creation', 'AI agents for creating infographics', 1800, 4, 'creative'),
('agents-for-ticket-management', 'Ticket Management', 'AI agents for managing support tickets', 3000, 4, 'customer'),
('agents-for-complaint-handling', 'Complaint Handling', 'AI agents for handling customer complaints', 1500, 4, 'customer'),
('agents-for-file-organization', 'File Organization', 'AI agents for organizing files and documents', 1500, 4, 'operations'),
('agents-for-invoice-generation', 'Invoice Generation', 'AI agents for generating invoices automatically', 1500, 4, 'finance'),
('agents-for-contract-analysis', 'Contract Analysis', 'AI agents for analyzing legal contracts', 1500, 4, 'finance'),
('agents-for-banner-ads', 'Banner Ads', 'AI agents for creating banner advertisements', 1500, 4, 'creative'),
('agents-for-thumbnail-creation', 'Thumbnail Creation', 'AI agents for creating video thumbnails', 1200, 4, 'creative'),
('agents-for-data-backup', 'Data Backup', 'AI agents for automated data backup', 1200, 4, 'operations'),
('agents-for-expense-reporting', 'Expense Reporting', 'AI agents for expense report generation', 1200, 4, 'finance')
ON CONFLICT (slug) DO NOTHING;

-- Create view for category page data
CREATE OR REPLACE VIEW category_with_counts AS
SELECT 
    ac.*,
    COUNT(a.id) as agent_count
FROM agent_categories ac
LEFT JOIN agents a ON a.primary_use_case = ac.slug
GROUP BY ac.id
ORDER BY ac.tier ASC, ac.search_volume DESC;

-- Create materialized view for performance
CREATE MATERIALIZED VIEW IF NOT EXISTS category_stats AS
SELECT 
    ac.slug,
    ac.name,
    ac.tier,
    ac.search_volume,
    ac.parent_category,
    COUNT(a.id) as agent_count,
    AVG(a.rating_avg) as avg_agent_rating,
    SUM(a.transaction_count) as total_transactions
FROM agent_categories ac
LEFT JOIN agents a ON a.primary_use_case = ac.slug
WHERE a.is_active = true OR a.is_active IS NULL
GROUP BY ac.id, ac.slug, ac.name, ac.tier, ac.search_volume, ac.parent_category
ORDER BY ac.tier ASC, ac.search_volume DESC;

-- Refresh materialized view (run this periodically)
-- REFRESH MATERIALIZED VIEW category_stats;

COMMENT ON TABLE agent_categories IS 'Top 100 AI agent search terms for category pages';
COMMENT ON COLUMN agent_categories.tier IS '1=ultra high (10K+), 2=high (3-6K), 3=medium (1.5-3K), 4=niche (1-1.5K)';
COMMENT ON COLUMN agents.protocol_support IS 'JSONB: {oasf: bool, a2a: bool, mcp: bool, slim: bool, agntcy: bool}';
