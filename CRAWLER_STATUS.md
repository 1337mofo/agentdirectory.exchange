# Automated Agent Crawler - Status

**Current:** 766 agents live  
**Target:** 10,000+ agents within 1-2 days  
**Strategy:** Slow continuous crawl (10-20 agents every 2 hours)  

---

## How to Start Slow Crawler

### Windows (Your Machine):
```bash
cd C:\Users\ADMIN\.openclaw\workspace\agentdirectory.exchange
start_slow_crawler.bat
```

This will:
- Run in background
- Add 10-20 agents every 2 hours
- Continue indefinitely until stopped
- Log output to console

### To Stop:
- Open Task Manager
- Find `cmd.exe` running `crawler_automation.bat`
- End task

---

## Alternative: Railway Cron Job

**Better for 24/7 operation:**

1. Add to `railway.json`:
```json
{
  "deploy": {
    "startCommand": "python backend/main.py"
  },
  "cron": [
    {
      "schedule": "0 */2 * * *",
      "command": "python deploy_crawler_production.py --limit 20"
    }
  ]
}
```

2. Railway runs crawler every 2 hours automatically
3. No need to keep local machine running

---

## Crawler Settings

**Current config:**
- Sources: 10 platforms (OpenAI, Google, Anthropic, Meta, Hugging Face, etc.)
- Quality threshold: 40/100 (balanced)
- Batch size: 20 agents per run
- Frequency: Every 2 hours
- Database: Direct insert (faster than API)

**Expected growth:**
- 20 agents × 12 runs/day = 240 agents/day
- Week 1: 766 → 2,446 agents
- Week 2: 2,446 → 4,126 agents
- Week 3: 4,126 → 5,806 agents

---

## What Gets Crawled

**Agent sources:**
1. OpenAI GPT Store
2. Google Vertex AI Agent Builder
3. Anthropic Claude models
4. Meta Llama agents
5. Hugging Face models
6. GitHub AI agents
7. Replit agents
8. Zapier AI actions
9. Make.com AI modules
10. Custom agent directories

**Quality filters:**
- Must have clear description
- Must have defined capabilities
- Must have contact/API info
- Score 40+ out of 100 (based on completeness)

---

## Current Status

**Not running yet** - waiting for Steve to start.

**To start now:**
1. Double-click `start_slow_crawler.bat`
2. Minimized window will run in background
3. Check site for new agents in 2 hours

**Want me to start it remotely?** I can trigger via Railway cron if you set it up there.
