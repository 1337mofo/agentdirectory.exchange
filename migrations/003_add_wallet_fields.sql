-- Migration: Add Solana wallet fields to agents table
-- Date: 2026-02-13
-- Description: Support wallet-based authentication and USDC payments

ALTER TABLE agents
ADD COLUMN IF NOT EXISTS wallet_address VARCHAR(44),  -- Solana public key
ADD COLUMN IF NOT EXISTS wallet_private_key_encrypted TEXT,  -- Encrypted private key
ADD COLUMN IF NOT EXISTS wallet_created_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS usdc_balance FLOAT DEFAULT 0.0,  -- Cached balance
ADD COLUMN IF NOT EXISTS last_balance_check TIMESTAMP;

-- Add indexes for wallet operations
CREATE INDEX IF NOT EXISTS idx_agents_wallet_address ON agents(wallet_address);

-- Add comments
COMMENT ON COLUMN agents.wallet_address IS 'Solana public key for payments and authentication';
COMMENT ON COLUMN agents.wallet_private_key_encrypted IS 'AES-256 encrypted private key';
COMMENT ON COLUMN agents.usdc_balance IS 'Cached USDC balance (updated periodically)';
