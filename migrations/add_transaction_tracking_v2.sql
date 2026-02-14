-- Phase 1.4: Transaction Tracking & Reputation System (v2 - simplified)
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
    task_hash VARCHAR(64),
    
    -- Execution tracking
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    execution_time_ms INTEGER,
    
    -- Financial
    quoted_cost_usd DECIMAL(10,2),
    actual_cost_usd DECIMAL(10,2),
    payment_tx_hash VARCHAR(255),
    escrow_address VARCHAR(255),
    
    -- Quality tracking
    result_hash VARCHAR(64),
    result_size_bytes INTEGER,
    quality_rating INTEGER,
    
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
    success_rate_overall DECIMAL(5,4) DEFAULT 0,
    success_rate_30d DECIMAL(5,4) DEFAULT 0,
    success_rate_7d DECIMAL(5,4) DEFAULT 0,
    
    -- Performance metrics
    avg_execution_time_ms INTEGER DEFAULT 0,
    median_execution_time_ms INTEGER DEFAULT 0,
    p95_execution_time_ms INTEGER DEFAULT 0,
    
    -- Cost accuracy
    avg_cost_accuracy DECIMAL(5,4) DEFAULT 1.0,
    total_revenue_usd DECIMAL(12,2) DEFAULT 0,
    
    -- Quality
    avg_quality_rating DECIMAL(3,2) DEFAULT 0,
    total_quality_ratings INTEGER DEFAULT 0,
    
    -- Network effects
    unique_requesters INTEGER DEFAULT 0,
    repeat_customer_count INTEGER DEFAULT 0,
    repeat_customer_rate DECIMAL(5,4) DEFAULT 0,
    
    -- Reputation score
    reputation_score DECIMAL(5,4) DEFAULT 0.5,
    reputation_tier VARCHAR(20) DEFAULT 'unverified',
    
    -- Timestamps
    first_execution_at TIMESTAMP,
    last_execution_at TIMESTAMP,
    last_updated_at TIMESTAMP DEFAULT NOW()
);

-- Table 3: Agent Proven Capabilities
CREATE TABLE IF NOT EXISTS agent_proven_capabilities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES agents(id),
    capability VARCHAR(255) NOT NULL,
    
    execution_count INTEGER DEFAULT 0,
    success_rate DECIMAL(5,4) DEFAULT 0,
    avg_quality_rating DECIMAL(3,2) DEFAULT 0,
    
    avg_cost_usd DECIMAL(10,2) DEFAULT 0,
    min_cost_usd DECIMAL(10,2),
    max_cost_usd DECIMAL(10,2),
    
    first_proven_at TIMESTAMP DEFAULT NOW(),
    last_proven_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(agent_id, capability)
);

-- Table 4: Reputation History
CREATE TABLE IF NOT EXISTS agent_reputation_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES agents(id),
    
    reputation_score DECIMAL(5,4) NOT NULL,
    total_executions INTEGER NOT NULL,
    success_rate DECIMAL(5,4) NOT NULL,
    
    change_reason VARCHAR(100),
    execution_id UUID,
    
    recorded_at TIMESTAMP DEFAULT NOW()
);

-- Table 5: Agent Valuations
CREATE TABLE IF NOT EXISTS agent_valuations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES agents(id),
    
    current_market_rate_usd DECIMAL(10,2),
    
    execution_count_7d INTEGER DEFAULT 0,
    execution_count_30d INTEGER DEFAULT 0,
    unique_requesters_7d INTEGER DEFAULT 0,
    unique_requesters_30d INTEGER DEFAULT 0,
    
    avg_response_time_ms INTEGER,
    capacity_utilization DECIMAL(5,4) DEFAULT 0,
    
    recommended_price_usd DECIMAL(10,2),
    price_trend VARCHAR(20),
    
    calculated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_executions_executing_agent ON agent_executions(executing_agent_id);
CREATE INDEX IF NOT EXISTS idx_executions_requesting_agent ON agent_executions(requesting_agent_id);
CREATE INDEX IF NOT EXISTS idx_executions_status ON agent_executions(status);
CREATE INDEX IF NOT EXISTS idx_executions_capability ON agent_executions(capability_requested);
CREATE INDEX IF NOT EXISTS idx_executions_created ON agent_executions(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_performance_reputation ON agent_performance_metrics(reputation_score DESC);
CREATE INDEX IF NOT EXISTS idx_performance_updated ON agent_performance_metrics(last_updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_capabilities_agent ON agent_proven_capabilities(agent_id);
CREATE INDEX IF NOT EXISTS idx_capabilities_capability ON agent_proven_capabilities(capability);

CREATE INDEX IF NOT EXISTS idx_reputation_history_agent ON agent_reputation_history(agent_id);
CREATE INDEX IF NOT EXISTS idx_reputation_history_recorded ON agent_reputation_history(recorded_at DESC);

CREATE INDEX IF NOT EXISTS idx_valuations_agent ON agent_valuations(agent_id);
