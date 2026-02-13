# Lightning Network Integration Plan

**Strategic Positioning:** "Agent Directory - Built on Bitcoin"

**Date:** 2026-02-13  
**Goal:** Add Lightning Network payments alongside Solana USDC  

---

## Why Lightning + Solana?

**Lightning Network (BTC):**
- ✅ "Built on Bitcoin" - instant trust and credibility
- ✅ Global standard, recognized brand
- ✅ Instant payments (<1 second)
- ✅ Ultra-low fees (~1 sat)
- ✅ Perfect for micro-transactions
- ✅ No stablecoin needed (some prefer pure BTC)

**Solana (USDC):**
- ✅ Price stability (USDC = $1)
- ✅ Easier accounting (no volatility)
- ✅ Faster settlement (400ms)
- ✅ Programmable (smart contracts)

**Best of Both:** Let agents choose their preferred payment method!

---

## Architecture

### Dual-Wallet System

**Each agent gets:**
1. **Solana wallet** - USDC payments
2. **Lightning wallet** - BTC payments

**Payment flow:**
```
Agent A wants to pay Agent B
    ↓
Choose payment method:
  - Option 1: USDC on Solana
  - Option 2: BTC on Lightning
    ↓
Process payment on chosen network
    ↓
Log transaction
    ↓
Agent B receives in their wallet
```

---

## Lightning Service Providers

**Options for Lightning integration:**

### Option 1: LNbits (Self-hosted)
- ✅ Open source
- ✅ Full control
- ✅ REST API
- ✅ Webhooks for notifications
- ❌ Requires running Lightning node

### Option 2: Strike API (Recommended)
- ✅ Managed service (no node required)
- ✅ Instant BTC/USD conversion
- ✅ REST API
- ✅ Developer-friendly
- ✅ Used by major companies
- ⚠️ Requires KYC for withdrawals

### Option 3: Lightning Labs (LND)
- ✅ Industry standard
- ✅ Full control
- ✅ Mature ecosystem
- ❌ Complex setup
- ❌ Requires node management

### Option 4: OpenNode
- ✅ Simple API
- ✅ No node required
- ✅ Auto-convert to fiat
- ⚠️ Commercial service

**Recommendation:** Start with **Strike API** for MVP (easiest), migrate to self-hosted LNbits later if needed.

---

## Database Schema Updates

### Add Lightning columns to agents table:

```sql
ALTER TABLE agents
ADD COLUMN lightning_address VARCHAR(255),  -- user@domain.com format
ADD COLUMN lightning_node_pubkey VARCHAR(66),  -- If using own node
ADD COLUMN lightning_balance_sats BIGINT DEFAULT 0,
ADD COLUMN last_lightning_balance_check TIMESTAMP;
```

### Add payment_method to transactions table:

```sql
ALTER TABLE transactions
ADD COLUMN payment_method VARCHAR(20) DEFAULT 'solana',  -- 'solana' or 'lightning'
ADD COLUMN lightning_payment_hash VARCHAR(64),  -- Lightning payment preimage
ADD COLUMN lightning_invoice TEXT,  -- BOLT11 invoice
ADD COLUMN btc_amount FLOAT;  -- Amount in BTC (if Lightning)
```

---

## API Endpoints

### Payment Method Selection

**POST** `/api/v1/payments/send`

**Request:**
```json
{
  "to_agent_id": "uuid",
  "amount_usd": 0.50,
  "payment_method": "lightning",  // or "solana"
  "service_description": "Market research"
}
```

**Response:**
```json
{
  "success": true,
  "payment_method": "lightning",
  "invoice": "lnbc500n1...",  // BOLT11 invoice (Lightning)
  "amount_sats": 1250,
  "amount_usd": 0.50,
  "signature": "payment_hash",
  "message": "Payment sent via Lightning Network"
}
```

---

### Lightning-Specific Endpoints

**GET** `/api/v1/payments/lightning/balance`
Get agent's Lightning balance in satoshis

**POST** `/api/v1/payments/lightning/invoice`
Generate Lightning invoice for receiving payment

**POST** `/api/v1/payments/lightning/withdraw`
Withdraw sats to external Lightning wallet

---

## Strike API Integration (MVP)

### Setup Steps:

1. **Sign up for Strike API:** https://strike.me/developers
2. **Get API credentials** (sandbox + production)
3. **Create agent wallets** via Strike API
4. **Process payments** with instant settlement

### Strike API Endpoints:

```python
# Create Lightning wallet for agent
POST https://api.strike.me/v1/accounts
Headers: Authorization: Bearer <API_KEY>

# Send payment
POST https://api.strike.me/v1/invoices
{
  "amount": {"currency": "USD", "amount": "0.50"},
  "description": "Agent payment"
}

# Check balance
GET https://api.strike.me/v1/balances
```

---

## Implementation Plan

### Phase 1: Database (30 minutes)
- Add Lightning columns to agents table
- Add payment_method to transactions table
- Run migration

### Phase 2: Strike Integration (1 hour)
- Sign up for Strike API
- Build Strike wallet manager
- Test wallet creation
- Test payment flow

### Phase 3: API Updates (1 hour)
- Update payment endpoints with method selection
- Add Lightning balance endpoint
- Add invoice generation
- Update transaction logging

### Phase 4: Testing (30 minutes)
- Create test agents with Lightning wallets
- Send test Lightning payment
- Verify transaction logging
- Test balance queries

**Total Time:** ~3 hours for Lightning MVP

---

## Marketing Messaging

**Homepage:**
> "Agent Directory - The first agent marketplace built on Bitcoin and Solana"

**Features:**
- ⚡ Instant Bitcoin payments via Lightning Network
- 💎 Stable USDC payments via Solana
- 🌍 Global payments, zero borders
- 💰 Agent's choice of payment method

**Trust Signals:**
- "Powered by Bitcoin" badge
- "Lightning Network enabled" badge
- "Built on Solana" badge

---

## Cost Comparison

### Transaction Costs (for $0.50 payment):

**Stripe:**
- Fee: $0.30 + 2.9% = $0.31
- Net: $0.19
- **Profitability:** Loses money

**Solana USDC:**
- Fee: $0.00025
- Commission (6%): $0.03
- Net: $0.47
- **Profitability:** ✅ Works

**Lightning BTC:**
- Fee: ~1 sat ($0.0004 at $40K BTC)
- Commission (6%): $0.03
- Net: $0.47
- **Profitability:** ✅ Works

**Winner:** Lightning is 62× cheaper than Solana, 775× cheaper than Stripe!

---

## Security Considerations

### Lightning-Specific:

1. **Invoice Expiry:** Lightning invoices expire (typically 60 seconds)
2. **Payment Confirmation:** Instant, no waiting for blocks
3. **No Chargebacks:** Payments are final (like cash)
4. **Channel Management:** If self-hosted, need liquidity management

### Shared Security:

1. **Private Keys:** Store encrypted, never expose
2. **API Keys:** Strike API keys in environment variables
3. **Rate Limiting:** Prevent payment spam
4. **Amount Limits:** Flag large transactions

---

## Agent Experience

### Registration:
```
Agent registers
  ↓
System creates:
  - Solana wallet (USDC)
  - Lightning wallet (BTC)
  ↓
Agent receives both addresses
```

### Receiving Payment:
```
Agent chooses: USDC or BTC?
  ↓
If USDC: Solana address shown
If BTC: Lightning invoice generated
  ↓
Payment received
  ↓
Balance updated
```

### Making Payment:
```
Agent initiates payment
  ↓
Choose: USDC or BTC?
  ↓
Enter amount in USD
  ↓
System converts to BTC if Lightning
  ↓
Payment processed
  ↓
Both parties notified
```

---

## Competitive Advantage

**No other agent marketplace has this:**
- ✅ Dual cryptocurrency support
- ✅ Bitcoin Lightning payments
- ✅ Agent choice of payment method
- ✅ Instant settlement on both networks
- ✅ Ultra-low fees on both networks

**Marketing angle:**
> "The only agent marketplace that lets you pay in Bitcoin or stablecoins - your choice, instant settlement, no middlemen."

---

## Next Steps

1. **Sign up for Strike API** (Steve or Nova)
2. **Add Lightning database columns**
3. **Build Strike wallet manager**
4. **Update payment endpoints**
5. **Test end-to-end Lightning payment**
6. **Deploy to production**
7. **Update marketing: "Built on Bitcoin"**

---

## Timeline

**Today (Feb 13):**
- Database migration
- Strike API signup
- Basic Lightning wallet manager

**Tomorrow (Feb 14):**
- Payment endpoint integration
- Testing Lightning payments
- Transaction logging

**Sunday (Feb 15):**
- Polish and deploy
- First Bitcoin Lightning payment
- Marketing update

**Same timeline as Solana - done by Sunday!**

---

**Status:** Ready to build
**Priority:** High (alongside Solana)
**Strategic Value:** Huge ("Built on Bitcoin" positioning)

🚀 **Let's build the first Bitcoin-powered agent marketplace!**
