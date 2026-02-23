-- Migration 008: Add Anti-Abuse Rate Limiting
-- Implements Boots' anti-abuse strategy: 50 free calls, 5/hour refill, IP tracking

-- Add rate limiting columns to agents table
ALTER TABLE agents ADD COLUMN IF NOT EXISTS free_calls_total INTEGER DEFAULT 50;
ALTER TABLE agents ADD COLUMN IF NOT EXISTS free_calls_remaining INTEGER DEFAULT 50;
ALTER TABLE agents ADD COLUMN IF NOT EXISTS hourly_rate_limit INTEGER DEFAULT 5;
ALTER TABLE agents ADD COLUMN IF NOT EXISTS hourly_calls_count INTEGER DEFAULT 0;
ALTER TABLE agents ADD COLUMN IF NOT EXISTS hourly_reset_at TIMESTAMP DEFAULT NOW();
ALTER TABLE agents ADD COLUMN IF NOT EXISTS signup_ip_address VARCHAR(45);  -- IPv6 max length
ALTER TABLE agents ADD COLUMN IF NOT EXISTS daily_spending_exposure FLOAT DEFAULT 0.0;

-- Add paid credits tracking
ALTER TABLE agents ADD COLUMN IF NOT EXISTS paid_calls_remaining INTEGER DEFAULT 0;

-- Create IP signup tracking table
CREATE TABLE IF NOT EXISTS ip_signup_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ip_address VARCHAR(45) NOT NULL,
    signup_date DATE NOT NULL,
    signup_count INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(ip_address, signup_date)
);

CREATE INDEX IF NOT EXISTS idx_ip_tracking_ip_date ON ip_signup_tracking(ip_address, signup_date);

-- Create disposable email domains blacklist table
CREATE TABLE IF NOT EXISTS disposable_email_domains (
    id SERIAL PRIMARY KEY,
    domain VARCHAR(255) NOT NULL UNIQUE,
    added_at TIMESTAMP DEFAULT NOW(),
    source VARCHAR(100)  -- 'manual', 'blocklist_import', 'detected'
);

CREATE INDEX IF NOT EXISTS idx_disposable_domains ON disposable_email_domains(domain);

-- Seed common disposable email domains (top 50 most common)
INSERT INTO disposable_email_domains (domain, source) VALUES
('tempmail.com', 'blocklist_import'),
('10minutemail.com', 'blocklist_import'),
('guerrillamail.com', 'blocklist_import'),
('mailinator.com', 'blocklist_import'),
('throwaway.email', 'blocklist_import'),
('temp-mail.org', 'blocklist_import'),
('fakeinbox.com', 'blocklist_import'),
('maildrop.cc', 'blocklist_import'),
('getnada.com', 'blocklist_import'),
('trashmail.com', 'blocklist_import'),
('yopmail.com', 'blocklist_import'),
('sharklasers.com', 'blocklist_import'),
('grr.la', 'blocklist_import'),
('guerrillamail.biz', 'blocklist_import'),
('guerrillamail.de', 'blocklist_import'),
('spam4.me', 'blocklist_import'),
('mailnesia.com', 'blocklist_import'),
('mytrashmail.com', 'blocklist_import'),
('tempinbox.com', 'blocklist_import'),
('mintemail.com', 'blocklist_import'),
('jetable.org', 'blocklist_import'),
('mailcatch.com', 'blocklist_import'),
('throwawaymail.com', 'blocklist_import'),
('emailondeck.com', 'blocklist_import'),
('dispostable.com', 'blocklist_import'),
('spamgourmet.com', 'blocklist_import'),
('incognitomail.com', 'blocklist_import'),
('anonbox.net', 'blocklist_import'),
('mohmal.com', 'blocklist_import'),
('anonymbox.com', 'blocklist_import'),
('emailsensei.com', 'blocklist_import'),
('receivemailonline.net', 'blocklist_import'),
('getairmail.com', 'blocklist_import'),
('tempr.email', 'blocklist_import'),
('inboxbear.com', 'blocklist_import'),
('trbvm.com', 'blocklist_import'),
('disposableemailaddresses.com', 'blocklist_import'),
('spamex.com', 'blocklist_import'),
('despammed.com', 'blocklist_import'),
('fastmail.fm', 'blocklist_import'),
('deadaddress.com', 'blocklist_import'),
('easytrashmail.com', 'blocklist_import'),
('spamfree24.org', 'blocklist_import'),
('bugmenot.com', 'blocklist_import'),
('spamavert.com', 'blocklist_import'),
('dontreg.com', 'blocklist_import'),
('spamhereplease.com', 'blocklist_import'),
('spam.la', 'blocklist_import'),
('temporaryemail.net', 'blocklist_import'),
('24hourmail.com', 'blocklist_import')
ON CONFLICT (domain) DO NOTHING;

-- Create daily platform spending tracking table
CREATE TABLE IF NOT EXISTS daily_platform_spending (
    spending_date DATE PRIMARY KEY,
    total_free_calls INTEGER DEFAULT 0,
    total_spending_usd FLOAT DEFAULT 0.0,
    spending_cap_usd FLOAT DEFAULT 50.0,
    cap_reached BOOLEAN DEFAULT FALSE,
    cap_reached_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Update existing agents with default values
UPDATE agents 
SET 
    free_calls_total = 50,
    free_calls_remaining = 50,
    hourly_rate_limit = 5,
    hourly_calls_count = 0,
    hourly_reset_at = NOW(),
    daily_spending_exposure = 0.0,
    paid_calls_remaining = 0
WHERE free_calls_total IS NULL;

COMMENT ON TABLE ip_signup_tracking IS 'Tracks signups per IP per day - limit 5 signups/IP/day';
COMMENT ON TABLE disposable_email_domains IS 'Blacklist of disposable/temporary email domains';
COMMENT ON TABLE daily_platform_spending IS 'Tracks daily free tier spending exposure - cap at $50/day';
