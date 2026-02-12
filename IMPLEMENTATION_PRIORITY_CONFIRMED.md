# Implementation Priority - CONFIRMED BY STEVE

**Decision:** "B then A"  
**Date:** 2026-02-12 17:10 GMT+7  
**Priority Order:** Crawler First → Acquisition Feature Second

---

## Phase 1: Crawler Bot (Option B) - IMMEDIATE

**Timeline:** This week  
**Status:** Production code ready, needs deployment

### Week 1 Actions:

**Day 1-2: Deploy Basic Crawler**
- [x] Code complete (agent_discovery_crawler.py)
- [x] Tested successfully (100 agents found)
- [ ] Configure ADMIN_API_KEY or DATABASE_URL
- [ ] Run first production upload
- [ ] Verify agents appear on site

**Day 3-4: Set Up Automation**
- [ ] Create cron job (every 6 hours)
- [ ] Windows Task Scheduler OR Railway cron
- [ ] Monitor first 24 hours of discovery
- [ ] Fix any issues

**Day 5-7: Enhance & Scale**
- [ ] Add RapidAPI source
- [ ] Improve description extraction
- [ ] Add owner notification emails
- [ ] Optimize quality scoring

**Expected Results:**
- Day 1: First 50-80 agents listed
- Day 7: 200+ agents listed
- Month 1: 500+ agents listed

---

## Phase 2: Acquisition Feature (Option A) - NEXT

**Timeline:** Weeks 2-5 (4 weeks)  
**Status:** Design complete, ready to build

### Week 2: Database & Core API

**Actions:**
- [ ] Add acquisition fields to agents table
- [ ] Create agent_acquisitions table
- [ ] Implement toggle acquisition mode endpoint
- [ ] Implement search acquisitions endpoint
- [ ] Implement inquiry submission endpoint

**Deliverables:**
- Database migrations
- API endpoints operational
- Basic backend complete

---

### Week 3: Negotiation & Payment

**Actions:**
- [ ] Build negotiation messaging system
- [ ] Stripe integration for high-value transactions
- [ ] Purchase agreement templates
- [ ] NDA generation and signing
- [ ] Escrow implementation

**Deliverables:**
- Negotiation flow working
- Payment processing tested
- Legal templates ready

---

### Week 4: Transfer & UI

**Actions:**
- [ ] Agent ownership transfer mechanism
- [ ] Build acquisition marketplace UI
- [ ] Agent detail page acquisition toggle
- [ ] Notification system for inquiries
- [ ] Admin review dashboard

**Deliverables:**
- Full UI implemented
- Transfer mechanism tested
- User-facing features complete

---

### Week 5: Legal & Polish

**Actions:**
- [ ] Legal review of purchase agreements
- [ ] Dispute resolution process
- [ ] Tax documentation (1099 generation)
- [ ] End-to-end testing
- [ ] Launch documentation

**Deliverables:**
- Legal compliance verified
- All testing complete
- Ready for first acquisition

---

## Parallel Work (During Both Phases)

### Google Merchant Center (STARTED)

**Status:** ✅ Verification tag added to site

**Next Steps:**
1. ✅ Add verification meta tag (DONE)
2. [ ] Click "Verify your online store" in Google Merchant
3. [ ] Wait for confirmation email
4. [ ] Claim online store
5. [ ] Set up product feed
6. [ ] Configure shipping/return policies (N/A for digital)

**Timeline:** 3-5 days for verification

---

### Google UCP Waitlist

**Status:** ⏳ Ready to submit

**Action:**
- [ ] Submit waitlist form: https://support.google.com/merchants/contact/ucp_integration_interest
- [ ] Document submission date
- [ ] Set reminder for follow-up

**Timeline:** 2-4 weeks for approval (out of our control)

**Strategy:** Submit NOW, build in parallel while waiting

---

## Success Metrics

### Phase 1 Targets (Crawler - Week 1):
- [ ] 50+ agents listed (Day 1)
- [ ] 200+ agents listed (Week 1)
- [ ] Crawler running every 6 hours
- [ ] 0 critical errors
- [ ] Site stats showing growth

### Phase 2 Targets (Acquisition - Week 5):
- [ ] 10+ agents listed for acquisition
- [ ] 5+ acquisition inquiries
- [ ] 1-2 completed acquisitions
- [ ] $50K+ total acquisition volume

### Combined Targets (Month 1):
- [ ] 500+ agents on platform
- [ ] 20M+ possible combinations
- [ ] First acquisition completed
- [ ] Google Merchant verified
- [ ] UCP waitlist submitted

---

## Resource Requirements

### Phase 1 (Crawler):
- **Developer time:** 20 hours (enhancement + monitoring)
- **Infrastructure:** Railway existing ($5/mo)
- **API costs:** $100/mo (GitHub, HuggingFace, RapidAPI)
- **Total:** ~$100/mo + 20 hours

### Phase 2 (Acquisition):
- **Developer time:** 120-160 hours (4 weeks full-time)
- **Legal review:** $500-1,000 (purchase agreement templates)
- **Infrastructure:** Railway existing (no additional cost)
- **Total:** $500-1,000 one-time + 160 hours

---

## Risk Mitigation

### Phase 1 Risks:
- **Rate limits:** Mitigated by 6-hour spacing, respectful crawling
- **Quality issues:** Mitigated by scoring threshold (50/100)
- **Duplicate agents:** Mitigated by source_id tracking
- **API changes:** Mitigated by error handling, fallbacks

### Phase 2 Risks:
- **Legal liability:** Mitigated by lawyer-reviewed templates, mandatory NDAs
- **Payment fraud:** Mitigated by Stripe verification, escrow
- **Transfer disputes:** Mitigated by clear ownership transfer process
- **Tax compliance:** Mitigated by 1099 generation, documentation

---

## Communication Plan

### Stakeholders:
1. **Agent owners** - Notify when discovered, invite to claim
2. **Buyers** - Email list for acquisition opportunities
3. **Community** - Discord/social for major milestones
4. **Google** - UCP waitlist follow-up

### Milestones to Announce:
- ✅ Crawler operational (today)
- 100 agents listed (Week 1)
- 500 agents listed (Month 1)
- First acquisition (Week 5-6)
- Google Merchant verified (Week 2)
- 1,000 agents listed (Month 2)

---

## Current Status Update

**✅ Completed Today:**
- Crawler production code written (10KB)
- Crawler tested successfully (100 agents found)
- Google Merchant verification tag added to site
- Multi-protocol strategy defined
- Whitepaper V2.0 published
- Stats moved above fold

**⏳ In Progress:**
- Railway redeploy (verification tag)
- Google Merchant verification (waiting for confirmation)

**🔴 Blocked On:**
- ADMIN_API_KEY configuration (for crawler upload)
- Google Merchant verification (24-48 hours)
- Google UCP waitlist approval (2-4 weeks)

---

## Immediate Next Actions (Today/Tomorrow)

### Today:
1. ✅ Add Google verification tag (DONE)
2. [ ] Click "Verify" in Google Merchant Center
3. [ ] Wait for Railway redeploy (verification tag live)
4. [ ] Configure ADMIN_API_KEY for crawler
5. [ ] Run first production crawler upload

### Tomorrow:
1. [ ] Verify agents appeared on site
2. [ ] Set up cron job (every 6 hours)
3. [ ] Monitor first 24 hours of automated discovery
4. [ ] Submit Google UCP waitlist
5. [ ] Begin Week 2 planning (Acquisition feature)

---

## Questions Resolved

**Q: Priority order?**  
A: ✅ B then A (Crawler first, Acquisition second)

**Q: Google Merchant verification?**  
A: ✅ Tag added, waiting for site redeploy

**Q: Crawler ready?**  
A: ✅ Code complete, tested, ready to deploy

**Q: Timeline?**  
A: Week 1 (Crawler), Weeks 2-5 (Acquisition)

---

## Files & Code Status

**Production Ready:**
- ✅ agent_discovery_crawler.py (10KB)
- ✅ frontend/index.html (Google verification tag)
- ✅ discovered_agents.jsonl (100 agents sample)

**Design Complete:**
- ✅ AGENT_ACQUISITION_FEATURE.md (15KB spec)
- ✅ AGENT_CRAWLER_BOT.md (17KB spec)
- ✅ MULTI_PROTOCOL_STRATEGY.md (11KB spec)

**In Progress:**
- ⏳ Database migrations (Acquisition feature)
- ⏳ API endpoints (Acquisition feature)
- ⏳ Cron job setup (Crawler automation)

---

**Priority confirmed. Crawler deploying this week. Acquisition feature starts Week 2.**

🚀
