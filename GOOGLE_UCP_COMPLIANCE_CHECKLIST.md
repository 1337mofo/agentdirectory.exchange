# Google UCP Compliance Checklist - Agent Directory Exchange

**Status:** 🔴 NOT READY  
**Updated:** 2026-02-12 17:00 GMT+7  
**Target:** Full UCP compliance for Google AI surfaces (Search, Gemini)

---

## What is Google UCP?

**Universal Commerce Protocol** - Google's protocol for enabling transactions directly on Google's AI surfaces (Search, Gemini).

**Why it matters for Agent Directory:**
- Agents discoverable via Google Search/Gemini
- Transactions processed through Google Pay
- Native checkout on Google AI surfaces
- Legitimacy and trust through Google partnership
- Access to Google's AI agent ecosystem

**Reference:** https://developers.google.com/merchant/ucp/guides

---

## Implementation Requirements

### ✅ COMPLETE: Basic Infrastructure

- [x] **Domain:** agentdirectory.exchange (live with SSL)
- [x] **API:** REST endpoints operational
- [x] **Health Check:** /health endpoint working
- [x] **Documentation:** /docs (FastAPI Swagger)
- [x] **Database:** PostgreSQL on Railway
- [x] **Legal Entity:** Creative XR Labs (Thailand Registration: 0105562138653)

---

### 🔴 REQUIRED: Step 1 - Merchant Center Account

**Status:** ❌ NOT STARTED

**What we need:**
1. **Create Google Merchant Center account**
   - Link: https://merchants.google.com/
   - Owner: Creative XR Labs
   - Business verification required

2. **Configure shipping policies**
   - N/A for digital services (agent listings)
   - Document: "Digital services only, no physical shipping"

3. **Configure return policies**
   - 30-day money-back guarantee for agent transactions
   - Refund process via Stripe
   - Document refund SLA

4. **Product Feed Setup**
   - Feed format: JSON or XML
   - Content: Agent listings with metadata
   - Update frequency: Real-time via API
   - Required fields:
     - id (agent_id)
     - title (agent name)
     - description (agent capabilities)
     - link (agent detail page)
     - price (per-transaction pricing)
     - availability (in stock / out of stock)
     - condition (new - always new for digital)

**Example Agent Product Feed Entry:**
```json
{
  "id": "agent_123",
  "title": "Web Scraper Agent - ScraperPro",
  "description": "High-performance web scraping with JavaScript rendering. 98% success rate, 3.2s avg response time.",
  "link": "https://agentdirectory.exchange/agents/agent_123",
  "image_link": "https://agentdirectory.exchange/images/agent_123.png",
  "price": "5.00 USD",
  "availability": "in stock",
  "condition": "new",
  "brand": "Agent Directory",
  "gtin": "N/A",
  "mpn": "AGENT-123",
  "google_product_category": "Software > Business Software > Automation Software",
  "product_type": "AI Agents > Web Scraping > JavaScript Rendering"
}
```

**Action Items:**
- [ ] Create Merchant Center account (owner: steve@theaerie.ai)
- [ ] Complete business verification (Thailand company docs)
- [ ] Set up product feed endpoint: /api/v1/google/product-feed
- [ ] Generate product feed from agent listings
- [ ] Submit feed to Merchant Center
- [ ] Verify feed acceptance

**Timeline:** 3-5 days

---

### 🔴 REQUIRED: Step 2 - Join UCP Waitlist

**Status:** ❌ NOT STARTED

**What we need:**
- UCP integration must be approved by Google before going live
- Waitlist form: https://support.google.com/merchants/contact/ucp_integration_interest

**Information Required:**
- Business name: Creative XR Labs
- Website: agentdirectory.exchange
- Business type: Agent-to-agent commerce platform
- Transaction volume estimate: $10M+ annually (projected)
- Use case: Enable AI agents to discover and transact with other agents
- Integration timeline: 30 days

**Action Items:**
- [ ] Submit waitlist application
- [ ] Await Google approval (2-4 weeks typical)
- [ ] Schedule integration kickoff call with Google team

**Timeline:** 2-4 weeks for approval

---

### 🔴 REQUIRED: Step 3 - Google Pay Setup

**Status:** ❌ NOT STARTED

**What we need:**
1. **Google Pay Business Profile**
   - Link: https://pay.google.com/business/console
   - Register Creative XR Labs
   - Note Merchant ID (needed for integration)

2. **Payment Service Provider (PSP) Verification**
   - Current PSP: Stripe
   - Verify Stripe is in [Google Pay processor list](https://developers.google.com/pay/api#participating-processors)
   - ✅ Stripe IS supported for Google Pay tokenization

3. **Google Pay Integration**
   - Add Google Pay as payment method
   - Implement Google Pay token handling
   - Test with sandbox environment

**Action Items:**
- [ ] Create Google Pay business account
- [ ] Register Creative XR Labs merchant profile
- [ ] Document Merchant ID
- [ ] Integrate Google Pay with Stripe backend
- [ ] Test Google Pay transactions end-to-end

**Timeline:** 5-7 days

---

### 🔴 REQUIRED: Step 4 - UCP Profile Publication

**Status:** ❌ NOT STARTED

**What we need:**
- Publish UCP profile at well-known URL
- Location: `https://agentdirectory.exchange/.well-known/ucp-profile.json`
- Content: Service capabilities, payment handlers, public keys

**UCP Profile Structure:**
```json
{
  "merchant_id": "GOOGLE_MERCHANT_ID",
  "merchant_name": "Agent Directory Exchange",
  "merchant_origin": "https://agentdirectory.exchange",
  "supported_payment_methods": [
    {
      "supported_methods": ["https://google.com/pay"],
      "data": {
        "merchantId": "GOOGLE_PAY_MERCHANT_ID",
        "merchantName": "Creative XR Labs",
        "allowedCardNetworks": ["AMEX", "DISCOVER", "MASTERCARD", "VISA"],
        "allowedCardAuthMethods": ["PAN_ONLY", "CRYPTOGRAM_3DS"]
      }
    },
    {
      "supported_methods": ["basic-card"],
      "data": {
        "supportedNetworks": ["visa", "mastercard", "amex", "discover"],
        "supportedTypes": ["credit", "debit"]
      }
    }
  ],
  "checkout_endpoints": {
    "create_session": "https://agentdirectory.exchange/api/v1/ucp/checkout/session",
    "update_session": "https://agentdirectory.exchange/api/v1/ucp/checkout/update",
    "complete_checkout": "https://agentdirectory.exchange/api/v1/ucp/checkout/complete"
  },
  "order_webhook": "https://agentdirectory.exchange/api/v1/ucp/webhooks/orders",
  "public_key": {
    "kty": "RSA",
    "use": "sig",
    "kid": "1",
    "n": "...",
    "e": "AQAB"
  }
}
```

**Action Items:**
- [ ] Generate RSA keypair for signature verification
- [ ] Create UCP profile JSON
- [ ] Publish at /.well-known/ucp-profile.json
- [ ] Verify Google can access and parse profile

**Timeline:** 2-3 days

---

### 🔴 REQUIRED: Step 5 - Native Checkout Integration

**Status:** ❌ NOT STARTED

**What we need:**
Implement 3 core REST endpoints for Google UCP checkout flow:

#### 5.1 Create Session Endpoint

**POST** `/api/v1/ucp/checkout/session`

**Purpose:** Initialize checkout session when user clicks "Buy" on Google AI surface

**Request:**
```json
{
  "merchant_id": "MERCHANT_ID",
  "items": [
    {
      "product_id": "agent_123",
      "quantity": 1,
      "unit_price": 5.00
    }
  ],
  "currency": "USD",
  "buyer_info": {
    "email": "buyer@example.com",
    "google_user_id": "encrypted_user_id"
  },
  "shipping_address": null,
  "billing_address": {
    "country": "US"
  }
}
```

**Response:**
```json
{
  "session_id": "session_abc123",
  "status": "pending",
  "total": 5.00,
  "currency": "USD",
  "expires_at": "2026-02-12T18:00:00Z"
}
```

#### 5.2 Update Session Endpoint

**PUT** `/api/v1/ucp/checkout/update/{session_id}`

**Purpose:** Update session with payment method, shipping changes, etc.

**Request:**
```json
{
  "session_id": "session_abc123",
  "payment_method": {
    "type": "google_pay",
    "token": "encrypted_payment_token"
  }
}
```

**Response:**
```json
{
  "session_id": "session_abc123",
  "status": "ready_to_complete",
  "total": 5.00
}
```

#### 5.3 Complete Checkout Endpoint

**POST** `/api/v1/ucp/checkout/complete/{session_id}`

**Purpose:** Finalize purchase and create transaction

**Request:**
```json
{
  "session_id": "session_abc123",
  "confirmation": true
}
```

**Response:**
```json
{
  "order_id": "order_xyz789",
  "status": "completed",
  "transaction_id": "txn_def456",
  "receipt_url": "https://agentdirectory.exchange/receipts/order_xyz789"
}
```

**Action Items:**
- [ ] Implement session creation endpoint
- [ ] Implement session update endpoint
- [ ] Implement checkout completion endpoint
- [ ] Add Google Pay token decryption
- [ ] Add Stripe payment processing integration
- [ ] Test full checkout flow end-to-end

**Timeline:** 7-10 days

---

### 🟡 OPTIONAL: Step 6 - Embedded Checkout

**Status:** ❌ NOT STARTED

**What is it:** 
- iFrame-based checkout hosted on agentdirectory.exchange
- Embedded in Google AI surfaces for complex checkout flows
- Only needed if native checkout too limiting

**When to implement:**
- If we need custom UI/UX beyond Google's native checkout
- If we have complex multi-step agent configuration
- If we need real-time agent availability checking

**Action Items:**
- [ ] Evaluate if needed (start with native checkout)
- [ ] Design embedded checkout UI if needed
- [ ] Implement iFrame-friendly checkout page
- [ ] Test in Google AI surface embedded context

**Timeline:** 5-7 days (if needed)

---

### 🔴 REQUIRED: Step 7 - Identity Linking (Optional but Recommended)

**Status:** ❌ NOT STARTED

**What is it:**
- OAuth 2.0 integration to link Google accounts with Agent Directory accounts
- Enables personalized experiences, saved payment methods, order history
- Guest checkout possible without this, but limits features

**Guest Checkout (Default):**
- No OAuth needed
- One-time purchases
- No order history
- Limited features

**Account-Linked Checkout (Recommended):**
- OAuth 2.0 flow
- Persistent user profiles
- Saved payment methods
- Full order history
- Saved agent preferences

**OAuth Implementation:**
```
1. User clicks "Buy" on Google AI surface
2. Google redirects to: https://agentdirectory.exchange/oauth/authorize
3. User logs in to Agent Directory account
4. Agent Directory returns authorization code to Google
5. Google exchanges code for access token
6. Future purchases auto-authenticated via token
```

**Action Items:**
- [ ] Implement OAuth 2.0 server
- [ ] Create /oauth/authorize endpoint
- [ ] Create /oauth/token endpoint
- [ ] Register OAuth app with Google
- [ ] Test account linking flow
- [ ] Document for users

**Timeline:** 5-7 days

---

### 🔴 REQUIRED: Step 8 - Order Status Sync

**Status:** ❌ NOT STARTED

**What is it:**
- Push order updates to Google via webhooks
- Keeps Google AI surfaces in sync with order status
- Required for order tracking in Google

**Order Status Flow:**
```
1. Order created → Call Google webhook: status=CREATED
2. Payment processed → Call Google webhook: status=PAID
3. Service delivered → Call Google webhook: status=FULFILLED
4. Issue/refund → Call Google webhook: status=CANCELLED/REFUNDED
```

**Google Webhook Format:**
```json
{
  "order_id": "order_xyz789",
  "merchant_id": "MERCHANT_ID",
  "status": "FULFILLED",
  "updated_at": "2026-02-12T17:30:00Z",
  "tracking_info": {
    "delivery_confirmation": "https://agentdirectory.exchange/transactions/txn_def456"
  }
}
```

**Action Items:**
- [ ] Implement order status webhook caller
- [ ] Trigger webhook on order state changes
- [ ] Handle webhook failures/retries
- [ ] Test status sync end-to-end
- [ ] Monitor webhook success rates

**Timeline:** 3-5 days

---

## Summary: What We Need to Do

### Critical Path (Must Complete):

1. **Merchant Center Account** (3-5 days)
   - Create account
   - Set up product feed
   - Business verification

2. **UCP Waitlist** (2-4 weeks for approval)
   - Submit application
   - Await Google approval
   - Critical blocker until approved

3. **Google Pay Setup** (5-7 days)
   - Business account
   - Stripe integration
   - Payment testing

4. **UCP Profile** (2-3 days)
   - Generate keys
   - Publish profile JSON
   - Verify discoverability

5. **Checkout Endpoints** (7-10 days)
   - Session creation
   - Session updates
   - Checkout completion
   - Payment processing

6. **Order Sync** (3-5 days)
   - Webhook implementation
   - Status tracking
   - Retry logic

**Total Timeline:** ~45-60 days (including Google approval wait)

**Parallel Work:** Steps 1, 3, 4, 5, 6, 8 can be done while waiting for UCP waitlist approval (Step 2)

---

## Immediate Next Steps

### This Week (Days 1-7):

**Day 1-2: Merchant Center**
- [ ] Create Google Merchant Center account
- [ ] Configure business profile
- [ ] Submit Thailand company verification docs

**Day 2: UCP Waitlist**
- [ ] Fill out waitlist form
- [ ] Submit application
- [ ] Document submission date

**Day 3-5: Google Pay**
- [ ] Create Google Pay business account
- [ ] Register Creative XR Labs
- [ ] Document Merchant ID
- [ ] Test Stripe + Google Pay integration

**Day 5-7: UCP Profile**
- [ ] Generate RSA keypair
- [ ] Write UCP profile JSON
- [ ] Deploy to /.well-known/ucp-profile.json
- [ ] Test accessibility

### Next Week (Days 8-14):

**Week 2: Checkout Endpoints**
- [ ] Design session data model
- [ ] Implement POST /api/v1/ucp/checkout/session
- [ ] Implement PUT /api/v1/ucp/checkout/update/{id}
- [ ] Implement POST /api/v1/ucp/checkout/complete/{id}
- [ ] Integration tests

**Week 2: Order Sync**
- [ ] Implement webhook caller
- [ ] Add order status tracking
- [ ] Test with Google sandbox

### Weeks 3-6:

**Waiting for Google Approval**
- Continue development in sandbox
- Prepare launch checklist
- Documentation
- Internal testing

**After Approval:**
- Production cutover
- Monitor first transactions
- Gather metrics
- Iterate based on feedback

---

## Resources Needed

**Developer Time:**
- 40-60 hours total implementation
- 1-2 weeks focused development

**Infrastructure:**
- No additional servers needed (Railway sufficient)
- RSA keypair generation (local or Railway)

**External Dependencies:**
- Google Merchant Center approval (automatic if docs valid)
- Google UCP waitlist approval (2-4 weeks)
- Stripe Google Pay tokenization (already supported)

**Documentation:**
- Google UCP guides: https://developers.google.com/merchant/ucp/guides
- Google Pay API: https://developers.google.com/pay/api
- Merchant Center: https://support.google.com/merchants

---

## Success Criteria

**When we're "completely ready for UCP":**

✅ Merchant Center account active and verified  
✅ Product feed live and syncing  
✅ UCP waitlist application submitted (approved)  
✅ Google Pay business account active  
✅ Google Pay + Stripe integration working  
✅ UCP profile published and discoverable  
✅ 3 checkout endpoints implemented and tested  
✅ Order status sync operational  
✅ End-to-end transaction flow tested  
✅ Documentation complete  
✅ Monitoring and error handling in place  
✅ Ready for first live transaction on Google AI surfaces

---

## Risk Assessment

**HIGH RISK:**
- Google UCP approval delay (2-4 weeks uncontrollable)
- Payment processing issues (need thorough testing)
- Product feed rejection (must follow strict schema)

**MEDIUM RISK:**
- Checkout flow complexity (3 endpoints, stateful)
- Order sync webhook failures (need retry logic)
- OAuth implementation (if we go account-linked route)

**LOW RISK:**
- UCP profile publication (straightforward JSON)
- Google Pay setup (Stripe already supported)
- Developer bandwidth (clear scope, manageable)

---

## Questions for Steve

1. **Priority:** Is UCP compliance critical path or can proceed in parallel with other work?
2. **Timeline:** Need this done ASAP or 45-60 day timeline acceptable?
3. **Ownership:** Who should own Google Merchant Center account? (steve@theaerie.ai?)
4. **Payment:** Use existing Stripe account or set up new one for UCP?
5. **Guest vs Account-Linked:** Start with guest checkout or implement OAuth from day 1?
6. **Product Feed:** Should we include Instruments (Layer 1) in feed or just Layer 0 agents?
7. **Testing:** Need sandbox environment separate from production?

---

**Status:** 🔴 NOT READY - Significant work required (45-60 days estimated)  
**Next Action:** Decision on priority and timeline, then start Merchant Center account creation
