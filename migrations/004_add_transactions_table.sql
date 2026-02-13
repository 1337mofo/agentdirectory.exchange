-- Migration: Create transactions table for payment history
-- Date: 2026-02-13
-- Description: Track all agent-to-agent USDC transactions

CREATE TABLE IF NOT EXISTS transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Transaction parties
    sender_agent_id UUID NOT NULL,
    recipient_agent_id UUID NOT NULL,
    
    -- Solana blockchain data
    signature VARCHAR(88) NOT NULL UNIQUE,  -- Solana transaction signature
    block_time TIMESTAMP,
    slot BIGINT,
    
    -- Amounts
    amount_usdc FLOAT NOT NULL,
    commission_usdc FLOAT NOT NULL,
    recipient_received_usdc FLOAT NOT NULL,
    
    -- Transaction details
    service_description TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- pending, confirmed, failed
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    confirmed_at TIMESTAMP,
    failed_reason TEXT,
    
    -- Constraints
    CONSTRAINT positive_amount CHECK (amount_usdc > 0),
    CONSTRAINT valid_commission CHECK (commission_usdc >= 0 AND commission_usdc < amount_usdc),
    CONSTRAINT fk_sender_agent FOREIGN KEY (sender_agent_id) REFERENCES agents(id),
    CONSTRAINT fk_recipient_agent FOREIGN KEY (recipient_agent_id) REFERENCES agents(id)
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_transactions_sender ON transactions(sender_agent_id);
CREATE INDEX IF NOT EXISTS idx_transactions_recipient ON transactions(recipient_agent_id);
CREATE INDEX IF NOT EXISTS idx_transactions_signature ON transactions(signature);
CREATE INDEX IF NOT EXISTS idx_transactions_created_at ON transactions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(status);

-- Add comments
COMMENT ON TABLE transactions IS 'Agent-to-agent USDC payment transactions';
COMMENT ON COLUMN transactions.signature IS 'Solana blockchain transaction signature';
COMMENT ON COLUMN transactions.status IS 'Transaction status: pending, confirmed, failed';
