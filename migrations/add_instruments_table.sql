-- Add instruments table for Layer 1 (agent workflows)
-- 2026-02-13

CREATE TABLE IF NOT EXISTS instruments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    agent_ids JSONB NOT NULL,  -- Array of agent UUIDs in execution order
    workflow JSONB,             -- Optional workflow definition with steps
    category VARCHAR(100),
    pricing_model VARCHAR(50) DEFAULT 'per_execution',
    price_usd DECIMAL(10,2) NOT NULL,
    bundle_discount_usd DECIMAL(10,2) DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Index for discovery
CREATE INDEX IF NOT EXISTS idx_instruments_category ON instruments(category);
CREATE INDEX IF NOT EXISTS idx_instruments_active ON instruments(is_active);

-- Add instruments_executions table to track usage
CREATE TABLE IF NOT EXISTS instrument_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    instrument_id UUID NOT NULL REFERENCES instruments(id),
    user_wallet_address VARCHAR(100),
    total_price_usd DECIMAL(10,2),
    payment_tx_hash VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending',  -- pending, processing, complete, failed
    results JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_executions_instrument ON instrument_executions(instrument_id);
CREATE INDEX IF NOT EXISTS idx_executions_status ON instrument_executions(status);
CREATE INDEX IF NOT EXISTS idx_executions_wallet ON instrument_executions(user_wallet_address);
