-- Phase 1.4: Transaction Tracking & Reputation System
-- Creates tables to track agent execution performance
-- 2026-02-13

-- Table 1: Agent Executions (every task execution)
CREATE TABLE IF NOT EXISTS agent_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Parties
    requesting_agent_id VARCHAR(255) NOT NULL,
    executing_agent_id UUID NOT NULL REFERENCES agents(id),
    
    -- Task details
    capability_requested VARCHAR(255) NOT NULL,
    task_type VARCHAR(100),
    task_hash VARCHAR(64),  -- SHA256 of task input
    
    -- Execution tracking
    status VARCHAR(50) NOT NULL DEFAULT 'pending',  -- pending, processing, completed, failed, timeout
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    execution_time_ms INTEGER,
    
    -- Financial
    quoted_cost_usd DECIMAL(10,2),
    actual_cost_usd DECIMAL(10,2),
    payment_tx_hash VARCHAR(255),
    escrow_address VARCHAR(255),
    
    -- Quality tracking
    result_hash VARCHAR(64),  -- SHA256 of result
    result_size_bytes INTEGER,
    quality_rating INTEGER CHECK (quality_rating >= 1 AND quality_rating <= 5),
    
    -- Outcome
    success BOOLEAN,
    error_code VARCHAR(50),
    error_message TEXT,
    
    -- Metadata
    protocol_version VARCHAR(10) DEFAULT '1.0',
    callback_url TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Table 2: Agent Performance Metrics (aggregated stats per agent)
CREATE TABLE IF NOT EXISTS agent_performance_metrics (
    agent_id UUID PRIMARY KEY REFERENCES agents(id),
    
    -- Execution counts
    total_executions INTEGER DEFAULT 0,
    successful_executions INTEGER DEFAULT 0,
    failed_executions INTEGER DEFAULT 0,
    timeout_executions INTEGER DEFAULT 0,
    
    -- Success rates
    success_rate DECIMAL(5,4) DEFAULT 0,  -- 0.0000 to 1.0000
    last_30_days_success_rate DECIMAL(5,4) DEFAULT 0,
    last_7_days_success_rate DECIMAL(5,4) DEFAULT 0,
    
    -- Performance metrics
    avg_execution_time_ms INTEGER DEFAULT 0,
    median_execution_time_ms INTEGER DEFAULT 0,
    p95_execution_time_ms INTEGER DEFAULT 0,
    
    -- Cost accuracy
    avg_cost_accuracy DECIMAL(5,4) DEFAULT 1.0,  -- 1.0 = perfect accuracy
    total_revenue_usd DECIMAL(12,2) DEFAULT 0,
    
    -- Quality
    avg_quality_rating DECIMAL(3,2) DEFAULT 0,  -- 0.00 to 5.00
    total_quality_ratings INTEGER DEFAULT 0,
    
    -- Network effects
    unique_requesters INTEGER DEFAULT 0,
    repeat_customer_count INTEGER DEFAULT 0,
    repeat_customer_rate DECIMAL(5,4) DEFAULT 0,
    
    -- Reputation score (calculated)
    reputation_score DECIMAL(5,4) DEFAULT 0.5,  -- 0.0000 to 1.0000
    reputation_tier VARCHAR(20) DEFAULT 'unverified',  -- unverified, bronze, silver, gold, platinum
    
    -- Timestamps
    first_execution_at TIMESTAMP,
    last_execution_at TIMESTAMP,
    last_updated_at TIMESTAMP DEFAULT NOW()
);

-- Table 3: Agent Capabilities (what each agent can actually do, proven by transactions)
CREATE TABLE IF NOT EXISTS agent_proven_capabilities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES agents(id),
    capability VARCHAR(255) NOT NULL,
    
    -- Performance for this specific capability
    execution_count INTEGER DEFAULT 0,
    success_rate DECIMAL(5,4) DEFAULT 0,
    avg_quality_rating DECIMAL(3,2) DEFAULT 0,
    
    -- Pricing for this capability
    avg_cost_usd DECIMAL(10,2) DEFAULT 0,
    min_cost_usd DECIMAL(10,2),
    max_cost_usd DECIMAL(10,2),
    
    -- Timestamps
    first_proven_at TIMESTAMP DEFAULT NOW(),
    last_proven_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(agent_id, capability)
);

-- Table 4: Reputation History (track reputation changes over time)
CREATE TABLE IF NOT EXISTS agent_reputation_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES agents(id),
    
    reputation_score DECIMAL(5,4) NOT NULL,
    total_executions INTEGER NOT NULL,
    success_rate DECIMAL(5,4) NOT NULL,
    
    -- What changed
    change_reason VARCHAR(100),  -- execution_completed, execution_failed, rating_received
    execution_id UUID REFERENCES agent_executions(id),
    
    recorded_at TIMESTAMP DEFAULT NOW()
);

-- Table 5: Agent Valuations (market-derived pricing)
CREATE TABLE IF NOT EXISTS agent_valuations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES agents(id),
    
    -- Market pricing
    current_market_rate_usd DECIMAL(10,2),
    
    -- Demand indicators
    execution_count_7d INTEGER DEFAULT 0,
    execution_count_30d INTEGER DEFAULT 0,
    unique_requesters_7d INTEGER DEFAULT 0,
    unique_requesters_30d INTEGER DEFAULT 0,
    
    -- Supply indicators
    avg_response_time_ms INTEGER,
    capacity_utilization DECIMAL(5,4) DEFAULT 0,  -- 0 = idle, 1 = fully utilized
    
    -- Pricing recommendations
    recommended_price_usd DECIMAL(10,2),
    price_trend VARCHAR(20),  -- increasing, stable, decreasing
    
    -- Timestamps
    calculated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_executions_executing_agent ON agent_executions(executing_agent_id);
CREATE INDEX IF NOT EXISTS idx_executions_requesting_agent ON agent_executions(requesting_agent_id);
CREATE INDEX IF NOT EXISTS idx_executions_status ON agent_executions(status);
CREATE INDEX IF NOT EXISTS idx_executions_capability ON agent_executions(capability_requested);
CREATE INDEX IF NOT EXISTS idx_executions_created ON agent_executions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_executions_completed ON agent_executions(completed_at DESC);

CREATE INDEX IF NOT EXISTS idx_performance_reputation ON agent_performance_metrics(reputation_score DESC);
CREATE INDEX IF NOT EXISTS idx_performance_updated ON agent_performance_metrics(last_updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_capabilities_agent ON agent_proven_capabilities(agent_id);
CREATE INDEX IF NOT EXISTS idx_capabilities_capability ON agent_proven_capabilities(capability);

CREATE INDEX IF NOT EXISTS idx_reputation_history_agent ON agent_reputation_history(agent_id);
CREATE INDEX IF NOT EXISTS idx_reputation_history_recorded ON agent_reputation_history(recorded_at DESC);

CREATE INDEX IF NOT EXISTS idx_valuations_agent ON agent_valuations(agent_id);
CREATE INDEX IF NOT EXISTS idx_valuations_calculated ON agent_valuations(calculated_at DESC);

-- Function to update agent performance metrics after execution
CREATE OR REPLACE FUNCTION update_agent_performance_metrics()
RETURNS TRIGGER AS $$
BEGIN
    -- Only process completed or failed executions
    IF NEW.status IN ('completed', 'failed', 'timeout') THEN
        -- Update or insert performance metrics
        INSERT INTO agent_performance_metrics (agent_id, last_updated_at)
        VALUES (NEW.executing_agent_id, NOW())
        ON CONFLICT (agent_id) DO NOTHING;
        
        -- This will be calculated by a separate job for performance
        -- (Too complex for trigger)
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update metrics on execution completion
CREATE TRIGGER trigger_update_agent_metrics
AFTER INSERT OR UPDATE ON agent_executions
FOR EACH ROW
EXECUTE FUNCTION update_agent_performance_metrics();

-- Comments for documentation
COMMENT ON TABLE agent_executions IS 'Records every agent task execution for performance tracking';
COMMENT ON TABLE agent_performance_metrics IS 'Aggregated performance metrics per agent (calculated periodically)';
COMMENT ON TABLE agent_proven_capabilities IS 'Capabilities proven through actual successful executions';
COMMENT ON TABLE agent_reputation_history IS 'Historical reputation scores for trend analysis';
COMMENT ON TABLE agent_valuations IS 'Market-derived agent valuations and pricing recommendations';
