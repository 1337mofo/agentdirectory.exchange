# Legal & Compliance Roadmap
## Agent Directory Exchange - Implementation Plan

**Status:** Pre-revenue, wild west phase  
**Current Risk:** Low (marketplace, not financial services)  
**Priority:** Get basics in place before first transaction  

---

## PHASE 1: Essential Protection (BEFORE FIRST TRANSACTION)

**Timeline:** This week (Feb 13-16)  
**Cost:** $0 (templates) or $200-500 (lawyer review)  
**Priority:** 🔴 CRITICAL

### 1.1 Terms of Service
**What it covers:**
- Platform is marketplace only (not responsible for agent actions)
- No warranties or guarantees
- Limitation of liability
- User responsibilities
- Dispute resolution process
- Right to remove bad actors

**Draft status:** Need to create  
**Action:** Nova drafts → Steve reviews → Post to site  

---

### 1.2 Privacy Policy
**What it covers:**
- What data we collect (emails, transaction history, API logs)
- How we use it (platform operations only)
- Who we share with (Stripe for payments, that's it)
- User rights (access, delete, export data)
- GDPR/CCPA compliance

**Draft status:** Need to create  
**Action:** Nova drafts → Steve reviews → Post to site  

---

### 1.3 Refund Policy
**What it covers:**
- When refunds are available (agent didn't deliver)
- How to request refund (email within 30 days)
- What's not refundable (completed services)
- Dispute resolution (evidence-based)

**Draft status:** Need to create  
**Action:** Nova drafts → Steve reviews → Post to site  

---

### 1.4 Agent Guidelines
**What it covers:**
- Prohibited agents (illegal, harmful, fraudulent)
- Quality standards (must have description, pricing, contact)
- Verification requirements (basic vs verified tiers)
- Enforcement (warnings → suspension → ban)

**Draft status:** Need to create  
**Action:** Nova drafts → Steve reviews → Post to site  

---

### 1.5 Platform Disclaimers
**Where to add:**
- Homepage footer: "We are a marketplace. Not responsible for agent performance."
- Agent pages: "This agent is independently operated. Contact agent owner for support."
- Checkout page: "You are purchasing from [Agent Owner], facilitated by Agent Directory Exchange."

**Draft status:** Need to create  
**Action:** Add to all relevant pages  

---

**PHASE 1 DELIVERABLES:**
- ✅ Terms of Service (live on site)
- ✅ Privacy Policy (live on site)
- ✅ Refund Policy (live on site)
- ✅ Agent Guidelines (live on site)
- ✅ Disclaimers on all pages

**DEADLINE:** Feb 16 (before any marketing push)

---

## PHASE 2: Tax & Business Setup (FIRST $1K REVENUE)

**Timeline:** When first transactions happen (Week 2-3)  
**Cost:** $0-1,000 depending on complexity  
**Priority:** 🟡 HIGH

### 2.1 Sales Tax Collection
**What:** Enable Stripe Tax for automatic collection

**Steps:**
1. Log into Stripe dashboard
2. Enable "Stripe Tax" feature (automatic)
3. Set business address (Thailand)
4. Stripe handles calculation/collection by location

**Complexity:** Easy (Stripe does the work)  
**Cost:** Stripe Tax is included  
**Action:** Steve enables in Stripe dashboard  

---

### 2.2 Thai Tax Registration
**What:** Ensure Creative XR Labs is compliant

**Current status:** Company registered (0105562138653)  

**Need to verify:**
- ✅ VAT registration (7% Thailand VAT)
- ✅ Corporate income tax setup
- ❓ E-commerce license needed? (check with Thai accountant)

**Action:** 
- Steve: Check with existing Thai accountant
- Confirm quarterly tax filing schedule
- Set up bookkeeping system (spreadsheet minimum)

**Cost:** Accountant fees (varies)  

---

### 2.3 US Entity (Optional - For Tax Optimization)
**Question:** Do we need US LLC for US customers?

**Benefits:**
- Lower US tax withholding (treaty with Thailand)
- More credible to US customers
- Easier to work with US payment processors

**Drawbacks:**
- Extra paperwork
- Annual fees ($100-300/year)
- Need US tax filing (Form 5472)

**Decision point:** If >50% of revenue is from US customers  
**Timeline:** Can wait until $5K/mo revenue  

---

### 2.4 Record Keeping System
**What:** Track all transactions for tax purposes

**Minimum requirements:**
- Transaction date
- Buyer info
- Agent/service purchased
- Amount paid
- Commission taken
- Stripe fees
- Net revenue

**Solution:** Export from database monthly, keep in spreadsheet  
**Retention:** 7 years (most jurisdictions)  

**Action:** Set up monthly export script  

---

**PHASE 2 DELIVERABLES:**
- ✅ Stripe Tax enabled
- ✅ Thai tax compliance verified
- ✅ Transaction records system
- ⏳ US entity (only if needed)

**DEADLINE:** Within 30 days of first transaction

---

## PHASE 3: Risk Mitigation (FIRST $10K/MO REVENUE)

**Timeline:** Months 2-3  
**Cost:** $1,000-3,000  
**Priority:** 🟢 MEDIUM

### 3.1 Legal Review
**What:** Get actual lawyer to review everything

**Scope:**
- Review Terms of Service
- Review Privacy Policy
- Review Refund Policy
- Advise on liability issues
- Check compliance gaps

**How to find:**
- Upwork: Search "SaaS lawyer" or "marketplace legal"
- Cost: $500-1,500 for review
- Alternative: LegalZoom ($199 package)

**Action:** Once revenue is $5K/mo  

---

### 3.2 Insurance
**Types needed:**

**A. Cyber Liability Insurance**
- Covers: Data breach, hacking, privacy violations
- Cost: $500-1,500/year
- When: Once storing customer payment info (we don't, Stripe does)

**B. General Liability Insurance**
- Covers: Lawsuits, injuries, damages
- Cost: $500-1,000/year
- When: Once revenue is $10K/mo

**C. Errors & Omissions (E&O)**
- Covers: Professional mistakes, negligence
- Cost: $1,000-2,000/year
- When: If you're advising customers (not just marketplace)

**Total cost:** ~$2-3K/year  
**Action:** Get quotes when revenue hits $10K/mo  

---

### 3.3 Trademark Registration
**What:** Protect "Agent Directory Exchange" name

**Benefits:**
- Prevent copycats
- More credible to investors
- Asset value (can be sold)

**Cost:**
- DIY: $350 (USPTO filing fee)
- With lawyer: $1,000-2,000 (filing + search + strategy)

**Timeline:** 6-12 months to approve  
**Action:** File when revenue is consistent ($5K+/mo)  

---

### 3.4 Compliance Monitoring
**What:** Stay updated on new regulations

**How:**
- Subscribe to tech law newsletters
- Join platform operator communities
- Monitor EU AI Act implementation
- Watch for US AI legislation

**Cost:** Free (time investment)  
**Action:** Set up Google Alerts for "AI regulation" + "marketplace law"  

---

**PHASE 3 DELIVERABLES:**
- ✅ Lawyer-reviewed legal docs
- ✅ Insurance policies active
- ✅ Trademark filed
- ✅ Compliance monitoring system

**DEADLINE:** By month 3 or $10K/mo revenue (whichever first)

---

## PHASE 4: Scale Preparation (FIRST $50K/MO REVENUE)

**Timeline:** Months 6-12  
**Cost:** $10,000-50,000  
**Priority:** 🔵 LOW (far future)

### 4.1 International Expansion
**If expanding beyond US/Thailand/EU:**
- Legal entity in target country
- Local payment processing
- Compliance with local laws
- Language translations for legal docs

---

### 4.2 Financial Services Licensing
**If adding advanced features:**
- Agent ownership trading → Securities license?
- Escrow services → Money transmitter license?
- USDC payments → Crypto regulations?

**Action:** Consult with financial services lawyer BEFORE building features  

---

### 4.3 Enterprise Compliance
**If targeting large companies:**
- SOC 2 certification ($20-50K)
- ISO 27001 certification ($30-100K)
- HIPAA compliance (if health agents)
- PCI Level 1 (if processing huge volume)

**Action:** Only if enterprise sales require it  

---

**PHASE 4 DELIVERABLES:**
- Depends on growth trajectory
- Don't prematurely optimize

---

## Red Lines (Never Do These)

### ❌ **Absolutely Forbidden:**
1. **Store credit card data** (PCI nightmare)
2. **Promise guaranteed returns** (securities violation)
3. **Call agents "investments"** (triggers regulation)
4. **Ignore DMCA takedowns** (lose safe harbor)
5. **Process payments yourself** (money transmitter license required)
6. **Allow medical/legal advice agents without disclaimers** (professional liability)

### ⚠️ **Requires Legal Review First:**
1. Agent ownership trading (secondary market)
2. Holding customer funds in escrow
3. Cryptocurrency payments (USDC/Solana)
4. Launching in China (very restricted)
5. Adding AI-generated content to agents (copyright issues)

---

## Decision Tree: When Do I Need a Lawyer?

### **Self-service (templates) is fine when:**
- ✅ Pre-revenue or <$5K/mo
- ✅ Simple marketplace model
- ✅ Using Stripe for payments
- ✅ US/EU/Australia customers only

### **Get legal review when:**
- 🟡 Revenue hits $5K/mo consistently
- 🟡 First dispute/complaint received
- 🟡 Planning to fundraise (investors want clean docs)
- 🟡 Adding new payment methods

### **Get lawyer on retainer when:**
- 🔴 Revenue hits $50K/mo
- 🔴 Threatened with lawsuit
- 🔴 Expanding to new countries
- 🔴 Launching secondary market features

---

## Action Items (Prioritized)

### **THIS WEEK (Nova can do):**
1. Draft Terms of Service
2. Draft Privacy Policy  
3. Draft Refund Policy
4. Draft Agent Guidelines
5. Add disclaimer text to all pages

**Time:** 4-6 hours  
**Cost:** $0  

---

### **NEXT WEEK (Steve action required):**
6. Review all legal docs
7. Approve or request changes
8. Publish to site footer
9. Enable Stripe Tax in dashboard
10. Verify Thai tax compliance with accountant

**Time:** 2-3 hours  
**Cost:** $0 (maybe accountant fee)  

---

### **MONTH 2-3 (Once revenue exists):**
11. Get lawyer to review docs ($500-1,500)
12. Set up monthly accounting system
13. File trademark application ($350-2,000)
14. Get insurance quotes ($2-3K/year)

**Time:** 8-10 hours  
**Cost:** $3,000-6,000  

---

## Summary

**Current status:** Wild west, minimal risk  
**Immediate need:** Basic legal docs (Terms, Privacy, Refund)  
**Cost to launch safely:** $0 (templates) to $500 (lawyer review)  
**Long-term cost:** $3-5K/year once at scale  

**Bottom line:** Get Phase 1 done this week, worry about Phase 2+ once you have actual transactions happening.

---

**Ready to start? Want me to draft Terms of Service first?**
