# Option B - Automated Crawler with Admin API Key ✅

**Status:** READY TO DEPLOY  
**Created:** 2026-02-13 07:26 GMT+7  
**Prerequisite:** Option A (categories.html) COMPLETE ✅  

---

## What Is Option B?

**Automated crawler that:**
1. Discovers agents from HuggingFace + GitHub
2. Evaluates quality scores
3. Submits directly to database via authenticated API
4. Auto-approves high-quality agents (score ≥ 70)
5. Queues medium-quality agents for manual review (50-69)
6. Rejects low-quality agents (< 50)

**No manual upload needed - fully automated growth.**

---

## Step 1: Set Admin API Key in Railway

**Your Admin API Key:**
```
<YOUR_ADMIN_API_KEY_HERE>
```

**Add to Railway Environment Variables:**

1. Go to Railway dashboard: https://railway.app
2. Select project: `agentdirectory.exchange`
3. Go to **Variables** tab
4. Click **New Variable**
5. Add:
   ```
   Name: ADMIN_API_KEY
   Value: <YOUR_ADMIN_API_KEY_HERE>
   ```
6. Click **Add**
7. Railway will auto-redeploy with new environment variable

**⚠️ Keep this key secure! It grants full admin access to the API.**

---

## Step 2: Test API Authentication

**Once Railway has redeployed with the API key:**

```bash
# Test API key works
curl -X POST https://agentdirectory.exchange/api/v1/crawler/stats \
  -H "Authorization: Bearer <YOUR_ADMIN_API_KEY_HERE>"

# Expected response:
{
  "success": true,
  "total_discovered": 0,
  "by_source": {},
  "pending_review": 0,
  "auto_approved": 0,
  "average_quality_score": 0
}
```

If you get `401 Unauthorized`, the API key isn't set correctly in Railway.

---

## Step 3: Run Automated Crawler (Local)

**Set environment variable locally:**

**Windows PowerShell:**
```powershell
$env:ADMIN_API_KEY = "<YOUR_ADMIN_API_KEY_HERE>"
```

**Windows CMD:**
```cmd
set ADMIN_API_KEY=<YOUR_ADMIN_API_KEY_HERE>
```

**Run the crawler:**
```bash
cd C:\Users\ADMIN\.openclaw\workspace\agentdirectory.exchange
python crawler_with_api.py
```

**Expected output:**
```
🦅 Agent Directory Crawler with API Upload
============================================================
Started: 2026-02-13 07:30:00
API Base: https://agentdirectory.exchange
API Key: eagle_admin_fKT_2h8b...
============================================================

[HUGGINGFACE] Searching for agents (limit: 100)...
[HUGGINGFACE] Found 87 agents

[GITHUB] Searching for agent repositories (limit: 50)...
[GITHUB] Found 43 agents

[SUMMARY] Total discovered: 130 agents

[SUBMIT] Filtered 130 → 94 agents (quality >= 50)
[SUBMIT] Submitting 94 agents to https://agentdirectory.exchange/api/v1/crawler/submit
[SUBMIT] ✓ Success!
[SUBMIT]   Created: 87
[SUBMIT]   Skipped: 7

✅ Crawler completed successfully
   87 agents added to directory

============================================================
[STATS] Crawler Statistics:
  Total Discovered: 87
  Auto-Approved: 62
  Pending Review: 25
  Average Quality: 68.4
  By Source:
    - huggingface: 54
    - github: 33
============================================================

Finished: 2026-02-13 07:31:45
```

---

## Step 4: Schedule Automated Runs

**Windows Task Scheduler (Every 6 Hours):**

```batch
:: Create scheduled task
schtasks /create /tn "AgentDirectoryCrawler" /tr "C:\Python312\python.exe C:\Users\ADMIN\.openclaw\workspace\agentdirectory.exchange\crawler_with_api.py" /sc hourly /mo 6 /st 00:00

:: Set environment variable for task
:: Note: Must set ADMIN_API_KEY in system environment variables for scheduled task
```

**Or create a batch file:** `run_crawler_scheduled.bat`

```batch
@echo off
set ADMIN_API_KEY=<YOUR_ADMIN_API_KEY_HERE>
cd C:\Users\ADMIN\.openclaw\workspace\agentdirectory.exchange
python crawler_with_api.py >> crawler_scheduled.log 2>&1
```

Then schedule the batch file instead.

---

## Step 5: Monitor Crawler Activity

**Check crawler stats:**
```bash
curl -X GET https://agentdirectory.exchange/api/v1/crawler/stats \
  -H "Authorization: Bearer <YOUR_ADMIN_API_KEY_HERE>"
```

**Review pending agents:**
```bash
cd C:\Users\ADMIN\.openclaw\workspace\agentdirectory.exchange
python review_submissions.py
```

**Bulk approve pending high-quality agents:**
```bash
curl -X POST "https://agentdirectory.exchange/api/v1/crawler/approve-pending?min_quality_score=65&limit=100" \
  -H "Authorization: Bearer <YOUR_ADMIN_API_KEY_HERE>"
```

---

## How It Works

### Quality Scoring System

**Quality Score Calculation:**

**HuggingFace:**
```
base_score = 50
downloads_bonus = downloads / 100
likes_bonus = likes * 5
quality_score = min(100, base_score + downloads_bonus + likes_bonus)
```

**GitHub:**
```
base_score = 50
stars_bonus = stars / 10
forks_bonus = forks / 5
quality_score = min(100, base_score + stars_bonus + forks_bonus)
```

**Approval Thresholds:**
- **< 50:** Rejected (not submitted)
- **50-69:** Pending manual review
- **≥ 70:** Auto-approved (goes live immediately)

### API Flow

```
Crawler discovers agents
    ↓
Calculate quality score
    ↓
Filter: quality >= 50
    ↓
POST /api/v1/crawler/submit
    ↓
Check Authorization header
    ↓
Validate admin API key
    ↓
For each agent:
  - Check for duplicate (source_url)
  - If quality >= 70: auto-approve
  - If quality 50-69: pending_review
    ↓
Bulk insert to database
    ↓
Return summary (created/skipped)
```

---

## API Endpoints (Admin-Only)

### POST `/api/v1/crawler/submit`
**Submit batch of discovered agents**

**Headers:**
```
Authorization: Bearer <YOUR_ADMIN_API_KEY_HERE>
Content-Type: application/json
```

**Body:**
```json
{
  "agents": [
    {
      "name": "Agent Name",
      "description": "Agent description...",
      "source_url": "https://github.com/user/repo",
      "discovery_source": "github",
      "quality_score": 75,
      "agent_type": "Open Source Agent",
      "categories": ["automation", "ai"]
    }
  ],
  "crawler_run_id": "run_1707812400",
  "dry_run": false
}
```

**Response:**
```json
{
  "success": true,
  "message": "Processed 1 agents: 1 created, 0 skipped",
  "agents_submitted": 1,
  "agents_created": 1,
  "agents_skipped": 0,
  "created_ids": ["uuid-here"]
}
```

### GET `/api/v1/crawler/stats`
**Get crawler statistics**

**Headers:**
```
Authorization: Bearer <YOUR_ADMIN_API_KEY_HERE>
```

**Response:**
```json
{
  "success": true,
  "total_discovered": 87,
  "by_source": {
    "huggingface": 54,
    "github": 33
  },
  "pending_review": 25,
  "auto_approved": 62,
  "average_quality_score": 68.4
}
```

### POST `/api/v1/crawler/approve-pending`
**Bulk approve pending agents above quality threshold**

**Query params:**
- `min_quality_score`: Minimum score to approve (default: 60)
- `limit`: Max agents to approve (default: 100)

**Headers:**
```
Authorization: Bearer <YOUR_ADMIN_API_KEY_HERE>
```

**Response:**
```json
{
  "success": true,
  "message": "Approved 25 agents",
  "approved_count": 25,
  "approved_ids": ["uuid1", "uuid2", ...]
}
```

---

## Growth Projections

**With Option B automated crawler running every 6 hours:**

| Timeframe | Runs | Agents per Run | Total New | Cumulative |
|-----------|------|----------------|-----------|------------|
| Day 1     | 4    | ~80            | 320       | 2,330      |
| Week 1    | 28   | ~60 (avg)      | 1,680     | 3,690      |
| Month 1   | 120  | ~40 (avg)      | 4,800     | 6,810      |
| Month 3   | 360  | ~30 (avg)      | 10,800    | 12,820     |

**Note:** Agents per run decreases as duplicates increase, but quality improves.

---

## Comparison: A vs B vs C

| Feature | Option A (Direct DB) | Option B (API Crawler) ✅ | Option C (Public Form) |
|---------|---------------------|------------------------|----------------------|
| **Speed** | Instant | Automated | Manual review |
| **Quality Control** | None | Score-based | Human review |
| **Auth Required** | No | Yes (admin key) | No (public) |
| **Scalability** | Manual | Fully automated | Limited by review |
| **Spam Risk** | High | Low | Very low |
| **Best For** | Emergency bulk | Ongoing growth | Community trust |

**Current Status:**
- Option A ✅ Complete (categories.html live)
- Option B ✅ Ready (need to set Railway env var)
- Option C ✅ Complete (submission form live)

---

## Security Notes

### Admin API Key
- ✅ Stored in Railway environment variables (secure)
- ✅ Not committed to git (added to .gitignore)
- ✅ Required for all crawler endpoints
- ✅ Validated on every request
- ⚠️ Keep offline copy in secure password manager

### API Endpoints
- ✅ Admin-only routes require authentication
- ✅ Public routes (submission form) have no auth
- ✅ Rate limiting TODO (add before public crawler announcement)
- ✅ Input validation on all fields

### Quality Filter
- ✅ Prevents low-quality spam (< 50 score rejected)
- ✅ Auto-approval only for high quality (≥ 70)
- ✅ Manual review for medium quality (50-69)

---

## Next Steps

### Immediate (Required for Option B)
1. ✅ Admin API key generated
2. ⏳ Set `ADMIN_API_KEY` in Railway environment variables
3. ⏳ Wait for Railway auto-redeploy (~2 minutes)
4. ⏳ Test API authentication
5. ⏳ Run first crawler batch
6. ⏳ Verify agents appear on site

### Phase 2 (Optimization)
- [ ] Add rate limiting on crawler endpoints
- [ ] Implement crawler cooldown (avoid hammering sources)
- [ ] Add more discovery sources (PyPI, npm, etc.)
- [ ] Improve quality scoring algorithm
- [ ] Add agent categorization ML model

### Phase 3 (Scale)
- [ ] Deploy crawler on Railway as background worker
- [ ] Add Telegram notifications for crawler runs
- [ ] Create admin dashboard for crawler management
- [ ] Add analytics: agents/day, approval rates, source performance

---

## Files Created

### Backend API
- `backend/api/auth.py` - Admin API key authentication (3.9 KB)
- `backend/api/crawler_endpoints.py` - Crawler endpoints (8.8 KB)
- `backend/main.py` - Updated to include crawler router

### Crawler Scripts
- `crawler_with_api.py` - Automated crawler with API upload (9.5 KB)

### Configuration
- `.gitignore` - Protect secrets (0.5 KB)
- `ADMIN_API_KEY.txt` - Secure key storage (NOT committed) (0.3 KB)

### Documentation
- `OPTION_B_SETUP.md` - This file (setup instructions)

**Total:** 6 files, ~23 KB of new code

---

## Testing Checklist

### Before First Run
- [ ] Admin API key set in Railway
- [ ] Railway has redeployed
- [ ] API authentication tested (curl /crawler/stats)
- [ ] Local environment variable set
- [ ] Crawler script tested (dry_run mode first)

### After First Run
- [ ] Agents appear on https://agentdirectory.exchange
- [ ] Auto-approved agents are active
- [ ] Pending review agents are inactive
- [ ] No duplicates created
- [ ] Quality scores look reasonable
- [ ] Crawler stats endpoint returns correct counts

### Production Readiness
- [ ] Scheduled task configured
- [ ] Crawler logs being captured
- [ ] Error notifications configured
- [ ] API rate limits added
- [ ] Monitoring dashboard created

---

## Troubleshooting

### "Invalid API key" Error
**Problem:** Crawler returns 401 Unauthorized  
**Solution:** 
1. Check `ADMIN_API_KEY` is set in Railway
2. Railway must redeploy after adding env var
3. Verify key matches exactly (no extra spaces)
4. Check local env var is set: `echo %ADMIN_API_KEY%` (CMD) or `$env:ADMIN_API_KEY` (PowerShell)

### "No agents discovered" Warning
**Problem:** APIs return 0 results  
**Solution:**
1. Check internet connection
2. HuggingFace/GitHub APIs may be rate-limited
3. Try smaller batch sizes
4. Wait 1-2 hours between runs

### "All agents skipped" Issue
**Problem:** All agents marked as duplicates  
**Solution:**
1. Check database for existing agents with same source_url
2. May need to run with different search terms
3. Crawler working correctly - duplicates prevented

### Crawler Crashes
**Problem:** Python script exits with error  
**Solution:**
1. Check Python version (3.8+ required)
2. Install requests: `pip install requests`
3. Check API base URL is correct
4. Verify admin API key is valid

---

## Success Metrics

### Week 1
- [ ] 300+ agents auto-discovered
- [ ] 200+ auto-approved (quality ≥ 70)
- [ ] 100+ pending review (quality 50-69)
- [ ] 0 low-quality spam (< 50)
- [ ] Crawler runs 4x/day without errors

### Month 1
- [ ] 5,000+ agents in directory
- [ ] 80%+ auto-approval rate
- [ ] Crawler is primary growth channel
- [ ] Manual review queue manageable (<100 pending)

### Month 3
- [ ] 10,000+ agents in directory
- [ ] Multiple discovery sources integrated
- [ ] Quality score algorithm refined
- [ ] Crawler deployed as Railway background worker
- [ ] Agent Directory is largest agent catalog globally

---

## Conclusion

✅ **Option B is READY TO DEPLOY**

Once you set `ADMIN_API_KEY` in Railway:
1. Run `crawler_with_api.py` locally
2. Watch agents get auto-discovered and uploaded
3. High-quality agents go live immediately
4. Medium-quality agents queue for review
5. Growth runs on autopilot

**Status:** WAITING FOR RAILWAY ENV VAR  
**Next:** Set API key → Test → Schedule → Scale

🦅 **Agent Directory: Automated growth activated**
