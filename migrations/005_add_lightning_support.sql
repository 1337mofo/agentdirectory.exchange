-- Migration: Add Lightning Network support
-- Date: 2026-02-13
-- Description: Add Lightning wallet columns and dual-payment support

-- Add Lightning columns to agents table
ALTER TABLE agents
ADD COLUMN IF NOT EXISTS lightning_address VARCHAR(255),  -- user@strike.me format
ADD COLUMN IF NOT EXISTS lightning_node_pubkey VARCHAR(66),  -- Optional: if using own node
ADD COLUMN IF NOT EXISTS lightning_balance_sats BIGINT DEFAULT 0,  -- Balance in satoshis
ADD COLUMN IF NOT EXISTS last_lightning_balance_check TIMESTAMP;

-- Add payment method support to transactions table
ALTER TABLE transactions
ADD COLUMN IF NOT EXISTS payment_method VARCHAR(20) DEFAULT 'solana',  -- 'solana' or 'lightning'
ADD COLUMN IF NOT EXISTS lightning_payment_hash VARCHAR(64),  -- Lightning payment hash
ADD COLUMN IF NOT EXISTS lightning_invoice TEXT,  -- BOLT11 invoice
ADD COLUMN IF NOT EXISTS btc_amount FLOAT;  -- Amount in BTC (for Lightning payments)

-- Create indexes for Lightning queries
CREATE INDEX IF NOT EXISTS idx_agents_lightning_address ON agents(lightning_address);
CREATE INDEX IF NOT EXISTS idx_transactions_payment_method ON transactions(payment_method);
CREATE INDEX IF NOT EXISTS idx_transactions_lightning_hash ON transactions(lightning_payment_hash);

-- Add comments
COMMENT ON COLUMN agents.lightning_address IS 'Lightning address in user@domain format';
COMMENT ON COLUMN agents.lightning_balance_sats IS 'Lightning balance in satoshis (1 BTC = 100M sats)';
COMMENT ON COLUMN transactions.payment_method IS 'Payment method: solana (USDC) or lightning (BTC)';
COMMENT ON COLUMN transactions.lightning_payment_hash IS 'Lightning Network payment hash';
COMMENT ON COLUMN transactions.btc_amount IS 'Amount in Bitcoin (for Lightning payments)';
