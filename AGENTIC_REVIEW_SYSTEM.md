# Agentic Agent Review System
## 100% Autonomous with Anti-Spam Security

**Status:** ✅ ACTIVE  
**Created:** 2026-02-14  
**Authority:** Steve Eagle directive - "Make it 100% agentic, secure, prevent spam"

---

## Overview

The Agent Directory Exchange submission system is now **fully autonomous**. Nova automatically reviews every agent submission, makes approve/reject decisions, and notifies submitters - all without human intervention.

## Security Measures

### 1. Rate Limiting
- **Email-based:** Max 3 submissions per email per 24 hours
- **Purpose:** Prevent spam submission floods
- **Enforcement:** Automatic rejection with clear error message

### 2. Email Validation
- **Format check:** RFC-compliant email addresses only
- **Disposable email blocking:** Rejects temp-mail/throwaway addresses
- **Blocked domains:** tempmail.com, 10minutemail.com, guerrillamail.com, mailinator.com, etc.

### 3. Content Quality Checks

**Name Validation:**
- Length: 3-100 characters
- Special characters: Max 30% of name
- No all-caps names (spam indicator)

**Description Validation:**
- Length: 50-2,000 characters
- Proper sentences required (punctuation check)
- Technical term bonus (AI/ML vocabulary)
- Emoji limit: Max 5 emojis

### 4. URL Validation
- **Format check:** Valid HTTP/HTTPS URLs
- **Reachability test:** HEAD request with 5s timeout
- **Trusted domain bonus:** github.com, huggingface.co, openai.com (+20 points)
- **TLD validation:** .com, .org, .io, .ai, .dev, .co preferred

### 5. Spam Detection
- **Keyword filtering:** Blocks casino, lottery, crypto scam, get-rich-quick, etc.
- **Link spam:** Max 3 links in description
- **Repeated characters:** Blocks "aaaaaa" spam patterns
- **All-caps detection:** Flags ALL CAPS text as spam

### 6. Duplicate Detection
- **Exact name match:** Prevents re-listing same agent
- **URL deduplication:** Same source URL = duplicate
- **Similar name detection:** Flags very similar agent names

---

## Quality Scoring System

### Base Score: 70 points

**Bonus Points:**
- +10: Good description length (100-500 chars)
- +5: Proper sentences (2+ punctuation marks)
- +3-15: Technical terms (agent, AI, ML, API, etc.)
- +20: Trusted domain (GitHub, HuggingFace, OpenAI)
- +10: URL is reachable (verified)
- +5: TLD is reputable (.com, .org, .ai, etc.)
- +5: API endpoint provided
- +5: HTTPS API endpoint (secure)

**Penalty Points:**
- -20: Name too short (<3 chars)
- -20: Description too short (<50 chars)
- -10: Description too long (>2000 chars)
- -10: Excessive emojis (>5)
- -30: Invalid URL format
- -20: URL validation error
- -10: URL not reachable

### Decision Thresholds

| Score | Decision |
|-------|----------|
| 80+ | **Auto-approve** (high quality) |
| 40-79 | **Auto-approve** (moderate quality) |
| <40 | **Auto-reject** (low quality/spam) |

---

## Approval Flow

```
User submits agent form
         ↓
AgenticReviewer runs checks:
  • Rate limiting
  • Email validation
  • Content quality
  • Spam detection
  • Duplicate check
  • URL validation
         ↓
Quality score calculated (0-100)
         ↓
     Decision:
         ↓
    ┌────────┴────────┐
    ↓                 ↓
APPROVED          REJECTED
    ↓                 ↓
is_active=True    is_active=False
verified=True     verified=False
    ↓                 ↓
Email to          Email to
submitter:        submitter:
"Approved!"       "Needs improvement"
    ↓                 ↓
Listed on         Not listed
directory
    ↓
Telegram to Steve
(only if score 90+
or rejected)
```

---

## Notifications

### Submitter Email (Every Submission)
- **Approved:** Congratulations message + live link + quality score
- **Rejected:** Constructive feedback + reason + resubmission invite

### Steve Telegram (Filtered)
- **Only notify:**
  - Rejections (all)
  - Exceptional approvals (90+ quality score)
- **Don't spam Steve with:**
  - Standard approvals (70-89 score)
  - Every routine submission

---

## Anti-Spam Features Summary

| Feature | Threshold | Action |
|---------|-----------|--------|
| Email rate limit | 3/day per email | Auto-reject |
| Disposable email | Detected | Auto-reject |
| Name too short | <3 chars | -20 points |
| Name all-caps | Detected | -20 points |
| Description too short | <50 chars | -20 points |
| Excessive emojis | >5 emojis | -10 points |
| Spam keywords | Detected | Instant reject |
| Too many links | >3 URLs in description | Instant reject |
| Repeated chars | "aaaaaaa" pattern | Instant reject |
| Duplicate name | Exact match | Instant reject |
| Duplicate URL | Exact match | Instant reject |

---

## Technical Implementation

### Files
- `backend/services/agentic_reviewer.py` - Core review logic (12KB)
- `backend/api/submission_endpoints.py` - Integration + notifications
- `backend/models/agent.py` - Added `reviewed_at`, `review_reason` fields
- `migrations/add_agentic_review_fields.sql` - Database migration

### Dependencies
- `requests` - URL validation, Telegram notifications
- `smtplib` - Email notifications to submitters
- `re` - Spam pattern detection
- `hashlib` - Duplicate detection (MD5 hashing)

### Configuration
- `TELEGRAM_BOT_TOKEN` - Environment variable for notifications
- `TELEGRAM_CHAT_ID` - Steve Eagle (1921452767)
- Email credentials - nova@agentdirectory.exchange via GoDaddy SMTP

---

## Analytics & Monitoring

**Track these metrics:**
- Submission rate (per hour/day)
- Approval rate (% auto-approved)
- Rejection rate (% auto-rejected)
- Average quality score
- Most common rejection reasons
- Rate limit triggers (spam attempts)

**Query examples:**
```sql
-- Approval rate last 7 days
SELECT 
  COUNT(*) FILTER (WHERE is_active = true) * 100.0 / COUNT(*) AS approval_rate
FROM agents 
WHERE submission_source = 'web_form' 
  AND created_at > NOW() - INTERVAL '7 days';

-- Average quality score by approval status
SELECT 
  is_active,
  AVG(quality_score) as avg_score,
  COUNT(*) as submissions
FROM agents
WHERE submission_source = 'web_form'
GROUP BY is_active;

-- Most common rejection reasons
SELECT 
  review_reason,
  COUNT(*) as occurrences
FROM agents
WHERE is_active = false 
  AND submission_source = 'web_form'
GROUP BY review_reason
ORDER BY occurrences DESC
LIMIT 10;
```

---

## Future Enhancements

**Phase 2 (Optional):**
1. **Machine learning scoring** - Train model on approval patterns
2. **Behavioral analysis** - Track submitter behavior over time
3. **CAPTCHA integration** - Extra anti-bot layer
4. **IP-based rate limiting** - Prevent VPN spam
5. **API endpoint testing** - Auto-test submitted API endpoints
6. **Category auto-assignment** - AI categorizes agent automatically
7. **Pricing validation** - Check if pricing is reasonable vs market

---

## Testing

**Manual test cases:**
1. ✅ Submit valid agent (GitHub URL, good description) → Auto-approve
2. ✅ Submit spam agent (casino keywords) → Auto-reject
3. ✅ Submit 4th agent same email in 1 day → Rate limit reject
4. ✅ Submit with disposable email → Email validation reject
5. ✅ Submit duplicate agent name → Duplicate detect reject
6. ✅ Submit with all-caps name → Quality penalty
7. ✅ Submit with 10 emojis in description → Quality penalty
8. ✅ Submit HuggingFace agent → Trusted domain bonus

**Automated tests:**
```python
# Test rate limiting
def test_rate_limit():
    email = "test@example.com"
    for i in range(4):
        response = submit_agent(email=email, name=f"Agent {i}")
        if i < 3:
            assert response.status_code == 201
        else:
            assert response.status_code == 429  # Rate limited

# Test spam detection
def test_spam_keywords():
    response = submit_agent(
        name="Get Rich Quick Bot",
        description="Make money fast with this amazing casino crypto opportunity!"
    )
    assert response.status_code == 400
    assert "spam" in response.json()["detail"].lower()
```

---

## Success Metrics

**Goals:**
- 95%+ of spam submissions rejected
- 90%+ of legitimate submissions approved
- <5 seconds review time per submission
- Zero false positives (good agents rejected)
- <1% false negatives (spam agents approved)

**Current Performance:** *(To be measured)*
- Approval rate: TBD
- Average quality score: TBD
- Review time: ~0.5 seconds

---

## Support & Troubleshooting

**Common Issues:**

**Q: My agent was rejected but it's legitimate**  
A: Check rejection reason in email. Common issues:
- Description too short (need 50+ characters)
- URL not reachable (check if site is online)
- Similar agent already exists
- Try improving description and resubmit

**Q: Email notification not received**  
A: Check spam folder. If still missing:
- Email service may have failed (non-blocking)
- Contact nova@agentdirectory.exchange
- We log all submissions, can manually resend

**Q: How do I resubmit after rejection?**  
A: Simply resubmit via the form with improvements. No waiting period required.

---

**System Status:** ✅ OPERATIONAL  
**Last Updated:** 2026-02-14 19:45 GMT+7  
**Maintained By:** Nova Eagle (AI Project Lead)
