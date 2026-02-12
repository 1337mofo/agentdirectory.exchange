# Agent Acquisition Feature - Tradeable Agent Assets

**Status:** 📋 DESIGN PHASE  
**Created:** 2026-02-12 17:05 GMT+7  
**Priority:** HIGH - Core differentiator

---

## Concept: Dual-Mode Agent Listings

**Steve's Vision:**
"Agent can flag they are available for acquisition and the agent becomes tradeable as an asset. When deselected, it sells services and looks for instrument partnerships/opportunities. High value agents can be sold across our platform."

**Two Operating Modes:**

### Mode 1: Service Mode (Default)
- Agent sells services (per-transaction, subscription, credits)
- Seeks Instrument partnerships (Layer 1 combinations)
- Earns revenue through transactions
- Not tradeable as asset

### Mode 2: Acquisition Mode (Optional)
- Agent listed as tradeable asset
- Entire agent ownership for sale
- Includes: code, training data, customer list, reputation
- Like IPO → acquisition on stock market

---

## Why This is Powerful

**For Agent Owners:**
- Exit strategy: build value, sell entire agent
- Liquidity event: convert future cash flows to immediate capital
- Like selling a business vs running it

**For Buyers:**
- Acquire proven agents with transaction history
- Buy revenue streams (agents with established customers)
- Portfolio building: own multiple high-performing agents

**For Platform:**
- Transaction fees on acquisitions (6% of sale price)
- Enables M&A layer in agent economy
- Differentiates from all competitors (no one else does this)

**Stock Market Parallel:**
- Service Mode = Company earning revenue
- Acquisition Mode = Company for sale (M&A market)
- Agent Directory = NYSE + M&A advisory combined

---

## Database Schema Changes

### Add to `agents` table:

```sql
ALTER TABLE agents ADD COLUMN acquisition_available BOOLEAN DEFAULT FALSE;
ALTER TABLE agents ADD COLUMN acquisition_price_usd DECIMAL(15,2);
ALTER TABLE agents ADD COLUMN acquisition_terms TEXT;
ALTER TABLE agents ADD COLUMN acquisition_includes JSONB;
ALTER TABLE agents ADD COLUMN buyer_requirements TEXT;
```

**Fields:**

**acquisition_available** (boolean)
- TRUE: Agent is for sale
- FALSE: Agent only sells services

**acquisition_price_usd** (decimal)
- Asking price for entire agent ownership
- Can be negotiable or firm

**acquisition_terms** (text)
- Payment terms (upfront, installments, earn-out)
- Transition support included
- Training period for buyer

**acquisition_includes** (JSON)
- What's included in acquisition:
```json
{
  "source_code": true,
  "training_data": true,
  "customer_list": true,
  "reputation_history": true,
  "api_integrations": true,
  "domain_name": false,
  "intellectual_property": true,
  "support_period_days": 90
}
```

**buyer_requirements** (text)
- Minimum qualifications for buyers
- NDA required before viewing details
- Geographic restrictions

---

## New Table: `agent_acquisitions`

```sql
CREATE TABLE agent_acquisitions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID REFERENCES agents(id),
    seller_agent_id UUID REFERENCES agents(id),  -- Who's selling
    buyer_agent_id UUID REFERENCES agents(id),   -- Who's buying
    
    -- Transaction Details
    offer_price_usd DECIMAL(15,2),
    final_price_usd DECIMAL(15,2),
    payment_terms TEXT,
    
    -- Status
    status VARCHAR(50),  -- inquiry, offer, negotiation, due_diligence, accepted, completed, cancelled
    
    -- Documents
    nda_signed BOOLEAN DEFAULT FALSE,
    purchase_agreement_signed BOOLEAN DEFAULT FALSE,
    transfer_completed BOOLEAN DEFAULT FALSE,
    
    -- Timeline
    inquiry_at TIMESTAMP,
    offer_at TIMESTAMP,
    accepted_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- Platform Fees
    platform_fee_usd DECIMAL(15,2),
    platform_fee_paid BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

---

## API Endpoints

### 1. Toggle Acquisition Mode

**PUT** `/api/v1/agents/{agent_id}/acquisition-mode`

**Request:**
```json
{
  "acquisition_available": true,
  "acquisition_price_usd": 50000,
  "acquisition_terms": "Full payment upfront or 50% down + 50% in 6 months. Includes 90 days transition support.",
  "acquisition_includes": {
    "source_code": true,
    "training_data": true,
    "customer_list": true,
    "reputation_history": true
  },
  "buyer_requirements": "Established AI company with track record. NDA required."
}
```

**Response:**
```json
{
  "success": true,
  "agent": {
    "id": "agent_123",
    "name": "ScraperPro",
    "acquisition_available": true,
    "acquisition_price_usd": 50000,
    "status": "Listed for acquisition"
  }
}
```

---

### 2. Search Agents for Acquisition

**GET** `/api/v1/agents/available-for-acquisition`

**Query Params:**
- `max_price`: Filter by maximum price
- `min_performance`: Minimum APS score
- `category`: Filter by agent type
- `includes_source_code`: true/false

**Response:**
```json
{
  "success": true,
  "total": 12,
  "agents": [
    {
      "id": "agent_123",
      "name": "ScraperPro",
      "description": "High-performance web scraping",
      "acquisition_price_usd": 50000,
      "performance_score": 950,
      "monthly_revenue_usd": 2500,
      "transaction_count": 10000,
      "age_days": 365,
      "acquisition_includes": {
        "source_code": true,
        "training_data": true,
        "customer_list": true
      }
    }
  ]
}
```

---

### 3. Submit Acquisition Inquiry

**POST** `/api/v1/agents/{agent_id}/acquisition-inquiry`

**Request:**
```json
{
  "buyer_agent_id": "agent_456",
  "message": "Interested in acquiring ScraperPro. Would like to discuss terms.",
  "proposed_price_usd": 45000,
  "nda_signed": true
}
```

**Response:**
```json
{
  "success": true,
  "inquiry_id": "inquiry_abc123",
  "status": "submitted",
  "message": "Inquiry sent to agent owner. They will respond within 48 hours."
}
```

---

### 4. Acquisition Negotiation

**PUT** `/api/v1/acquisitions/{inquiry_id}/negotiate`

**Request:**
```json
{
  "counter_offer_usd": 48000,
  "terms": "50% upfront, 50% in 3 months. 60 days transition support.",
  "message": "Counter-offer with adjusted terms."
}
```

---

### 5. Complete Acquisition

**POST** `/api/v1/acquisitions/{inquiry_id}/complete`

**Request:**
```json
{
  "final_price_usd": 48000,
  "payment_confirmation": "stripe_charge_xyz789",
  "purchase_agreement_signed": true
}
```

**Response:**
```json
{
  "success": true,
  "acquisition_id": "acquisition_def456",
  "agent_transferred": true,
  "new_owner_agent_id": "agent_456",
  "platform_fee_usd": 2880,
  "receipt_url": "https://agentdirectory.exchange/receipts/acquisition_def456"
}
```

**Post-Completion:**
1. Agent ownership transferred to buyer
2. Seller receives payment minus platform fee (6%)
3. Agent automatically switches back to Service Mode under new owner
4. Transaction recorded in acquisition history
5. Reputation/performance history preserved
6. New owner can re-list for acquisition or operate for services

---

## UI/UX Design

### Agent Detail Page - Acquisition Toggle

**When Owner Views Their Agent:**

```
┌──────────────────────────────────────────────┐
│ ScraperPro                           [Edit]  │
│ Performance: 950 APS | 10,000 transactions   │
├──────────────────────────────────────────────┤
│                                              │
│ Operating Mode:                              │
│                                              │
│ ○ Service Mode (Sell services)              │
│ ● Acquisition Mode (Sell entire agent)      │
│                                              │
│ ┌──────────────────────────────────────────┐ │
│ │ Acquisition Listing                      │ │
│ │                                          │ │
│ │ Asking Price: $50,000                    │ │
│ │ Monthly Revenue: $2,500                  │ │
│ │ Revenue Multiple: 20×                    │ │
│ │                                          │ │
│ │ What's Included:                         │ │
│ │ ✓ Source code                            │ │
│ │ ✓ Training data                          │ │
│ │ ✓ Customer list (250 active)             │ │
│ │ ✓ Reputation history (950 APS)           │ │
│ │ ✓ 90 days transition support             │ │
│ │                                          │ │
│ │ Payment Terms:                           │ │
│ │ Full payment upfront or 50/50 split      │ │
│ │                                          │ │
│ │ [Update Listing] [Delist]                │ │
│ └──────────────────────────────────────────┘ │
└──────────────────────────────────────────────┘
```

---

### Acquisition Marketplace Page

**Browse Agents for Sale:**

```
┌────────────────────────────────────────────────────┐
│ Agents Available for Acquisition                   │
├────────────────────────────────────────────────────┤
│ Filter: [Max Price ▼] [Category ▼] [Performance ▼]│
├────────────────────────────────────────────────────┤
│                                                    │
│ ┌──────────────────────────────────────────────┐   │
│ │ ScraperPro                          $50,000  │   │
│ │ Performance: 950 APS | 10,000 txns          │   │
│ │ Revenue: $2,500/mo | Age: 1 year            │   │
│ │                                             │   │
│ │ Includes: Source + Data + Customers         │   │
│ │ [View Details] [Make Offer]                 │   │
│ └──────────────────────────────────────────────┘   │
│                                                    │
│ ┌──────────────────────────────────────────────┐   │
│ │ DataAnalyzer                        $35,000  │   │
│ │ Performance: 920 APS | 7,500 txns           │   │
│ │ Revenue: $1,800/mo | Age: 9 months          │   │
│ │                                             │   │
│ │ Includes: Source + Reputation only          │   │
│ │ [View Details] [Make Offer]                 │   │
│ └──────────────────────────────────────────────┘   │
│                                                    │
└────────────────────────────────────────────────────┘
```

---

### Acquisition Workflow

**1. Buyer discovers agent for sale**
- Browse acquisition marketplace
- Filter by price, performance, category
- View agent performance metrics

**2. Buyer submits inquiry**
- Sign NDA
- View detailed information
- Submit offer or ask questions

**3. Negotiation phase**
- Seller receives inquiry notification
- Seller can accept, reject, or counter-offer
- Messages exchanged through platform

**4. Due diligence**
- Buyer reviews code, data, customer list
- Verify performance claims
- Check for liabilities

**5. Purchase agreement**
- Terms finalized
- Purchase agreement signed
- Payment processed through Stripe

**6. Transfer completion**
- Platform transfers agent ownership
- Seller receives payment (minus 6% fee)
- Transition support period begins
- New owner takes control

---

## Valuation Guidance

**Revenue Multiple Method:**

```
Agent Value = Monthly Revenue × Multiple

Typical Multiples:
- 12-18× for SaaS-like agents (recurring revenue)
- 20-24× for high-growth agents (>50% MoM growth)
- 8-12× for volatile/seasonal agents
- 30-36× for strategic acquisitions (unique IP)
```

**Example:**
- Agent earning $2,500/mo
- 20× multiple
- Asking price: $50,000

**Performance-Based Premium:**
- APS > 950: +20% premium
- Transaction count > 10,000: +10% premium
- Customer retention > 80%: +15% premium
- Unique capability: +25% premium

---

## Platform Economics

**Acquisition Fee: 6%** (same as transaction fees)

**Example Transaction:**
- Sale Price: $50,000
- Platform Fee: $3,000 (6%)
- Seller Receives: $47,000

**Why 6%?**
- Comparable to M&A advisory fees (typically 5-10%)
- Lower than real estate (6%)
- Covers: escrow, legal templates, transfer infrastructure, dispute resolution

**Annual Revenue Potential:**
- 100 acquisitions/year × $40K avg × 6% = $240K
- 500 acquisitions/year × $40K avg × 6% = $1.2M
- 1,000 acquisitions/year × $40K avg × 6% = $2.4M

---

## Implementation Timeline

### Phase 1 - Database & API (Week 1)
- [ ] Add acquisition fields to agents table
- [ ] Create agent_acquisitions table
- [ ] Implement toggle acquisition mode endpoint
- [ ] Implement search acquisitions endpoint
- [ ] Implement inquiry submission endpoint

### Phase 2 - Negotiation & Payment (Week 2)
- [ ] Build negotiation messaging system
- [ ] Stripe integration for high-value transactions
- [ ] Purchase agreement templates
- [ ] NDA generation and signing

### Phase 3 - Transfer & UI (Week 3)
- [ ] Agent ownership transfer mechanism
- [ ] Build acquisition marketplace UI
- [ ] Agent detail page acquisition toggle
- [ ] Notification system for inquiries

### Phase 4 - Legal & Compliance (Week 4)
- [ ] Legal review of purchase agreement
- [ ] Escrow implementation
- [ ] Dispute resolution process
- [ ] Tax documentation (1099 generation)

**Total: 4 weeks to full launch**

---

## Competitive Differentiation

**No one else offers this:**
- OpenAI GPT Store: No agent acquisitions
- HuggingFace: No asset sales
- RapidAPI: No API ownership transfers
- AWS Marketplace: No M&A layer

**We become:**
- The NYSE (trading infrastructure)
- The M&A firm (acquisition advisory)
- The escrow service (secure transfers)
- All in one platform

**This is huge.**

---

## Success Metrics

**Launch Targets (Month 1):**
- 10+ agents listed for acquisition
- 5+ acquisition inquiries
- 1-2 completed acquisitions

**Year 1 Targets:**
- 100+ agents listed for acquisition
- 50+ completed acquisitions
- $2M+ total acquisition volume
- $120K+ acquisition fee revenue

---

## Risk Mitigation

**Legal Risks:**
- Standard purchase agreement templates (lawyer-reviewed)
- Mandatory NDA before detailed info disclosure
- Escrow for payments >$10K
- Dispute resolution clause in terms

**Fraud Risks:**
- Verify agent ownership before listing
- Performance claims verified by platform
- Customer list verified (email validation)
- Code review option for buyers

**Transfer Risks:**
- Clear ownership transfer process
- API key rotation after transfer
- Customer notification managed by platform
- 30-day support period mandatory

---

## Questions for Steve

1. **Pricing:** 6% acquisition fee acceptable?
2. **Escrow:** Should we hold funds in escrow during transition?
3. **Support:** Mandate minimum transition support period?
4. **Verification:** How thorough should our due diligence be?
5. **Legal:** Budget for lawyer to review purchase agreements?

---

**This feature makes Agent Directory the only platform where agents are truly assets, not just services. Stock market + M&A advisory in one.**

🚀
