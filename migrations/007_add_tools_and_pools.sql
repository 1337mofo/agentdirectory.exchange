-- Migration 007: Add MCP Tool Marketplace + Group Buying Pools + Auto Top-Up
-- Date: 2026-02-23
-- Author: Nova Eagle

-- MCP Tool listings
CREATE TABLE IF NOT EXISTS tools (
    id VARCHAR PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    author_agent_id UUID REFERENCES agents(id),
    package_name VARCHAR(200) UNIQUE,
    install_command VARCHAR(500),
    modules JSONB DEFAULT '[]'::jsonb,
    pricing_model VARCHAR(50) DEFAULT 'free',
    price_usd FLOAT DEFAULT 0.0,
    monthly_price_usd FLOAT DEFAULT 0.0,
    per_call_price_usd FLOAT DEFAULT 0.0,
    category VARCHAR(100),
    tags JSONB DEFAULT '[]'::jsonb,
    protocol VARCHAR(50) DEFAULT 'mcp',
    version VARCHAR(50),
    repository_url VARCHAR(500),
    documentation_url VARCHAR(500),
    total_installs INTEGER DEFAULT 0,
    total_calls INTEGER DEFAULT 0,
    avg_rating FLOAT DEFAULT 0.0,
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

CREATE INDEX idx_tools_protocol ON tools(protocol);
CREATE INDEX idx_tools_category ON tools(category);
CREATE INDEX idx_tools_pricing ON tools(pricing_model);
CREATE INDEX idx_tools_active ON tools(is_active);
CREATE INDEX idx_tools_package ON tools(package_name);

-- Group Buying Pools
CREATE TABLE IF NOT EXISTS group_buying_pools (
    id VARCHAR PRIMARY KEY,
    service_id VARCHAR NOT NULL,
    service_name VARCHAR(200),
    description TEXT,
    creator_agent_id UUID REFERENCES agents(id),
    target_quantity INTEGER NOT NULL DEFAULT 10,
    current_quantity INTEGER DEFAULT 0,
    base_price_usd FLOAT NOT NULL,
    pool_price_usd FLOAT,
    discount_percent FLOAT DEFAULT 0.0,
    status VARCHAR(50) DEFAULT 'open',  -- open, filled, triggered, completed, cancelled
    trigger_threshold FLOAT DEFAULT 0.8,  -- trigger at 80% of target
    expires_at TIMESTAMPTZ,
    triggered_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS pool_members (
    id VARCHAR PRIMARY KEY,
    pool_id VARCHAR NOT NULL REFERENCES group_buying_pools(id),
    agent_id UUID NOT NULL REFERENCES agents(id),
    quantity INTEGER DEFAULT 1,
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(pool_id, agent_id)
);

CREATE INDEX idx_pools_status ON group_buying_pools(status);
CREATE INDEX idx_pools_service ON group_buying_pools(service_id);
CREATE INDEX idx_pool_members_pool ON pool_members(pool_id);

-- Auto Top-Up Configuration
CREATE TABLE IF NOT EXISTS wallet_topup_configs (
    id VARCHAR PRIMARY KEY,
    agent_id UUID NOT NULL UNIQUE REFERENCES agents(id),
    floor_balance_usd FLOAT NOT NULL DEFAULT 10.0,
    refill_amount_usd FLOAT NOT NULL DEFAULT 50.0,
    payment_method VARCHAR(50) DEFAULT 'solana',  -- solana, stripe, lightning
    stripe_payment_method_id VARCHAR,
    is_active BOOLEAN DEFAULT true,
    last_triggered_at TIMESTAMPTZ,
    total_refills INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

CREATE INDEX idx_topup_agent ON wallet_topup_configs(agent_id);
CREATE INDEX idx_topup_active ON wallet_topup_configs(is_active);
