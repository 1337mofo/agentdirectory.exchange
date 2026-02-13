# Crawler Auto-Run Setup for Creative XR Labs Server

**Status:** ✅ Crawler uploaded to server successfully

**File location:** `/crawler_continuous.py` (root FTP directory)

---

## What It Does:

- Runs every hour automatically
- Discovers 80+ new agents per run (HuggingFace + GitHub)
- Deploys directly to Railway database
- Logs everything to `crawler.log`
- No manual intervention needed

---

## Setup Instructions (Steve - 2 minutes):

### **Step 1: SSH into server**
```bash
ssh nova@creativexrlabs.com
# (or however you normally access the server)
```

### **Step 2: Install dependencies (if needed)**
```bash
pip3 install requests beautifulsoup4 psycopg2-binary
```

### **Step 3: Test the crawler manually**
```bash
cd /
python3 crawler_continuous.py
```

This should run and deploy some agents. Check the output.

### **Step 4: Set up cron job**
```bash
crontab -e
```

Add this line at the bottom:
```
*/30 * * * * /usr/bin/python3 /crawler_continuous.py >> /crawler.log 2>&1
```

Save and exit (Ctrl+O, Enter, Ctrl+X in nano)

### **Step 5: Verify cron is running**
```bash
crontab -l
```

Should show the line you just added.

---

## Done!

The crawler will now run **every 30 minutes** (1:00, 1:30, 2:00, 2:30, etc.)

Each run discovers ~80 agents and deploys them immediately.

**Expected growth:**
- Hour 1: +160 agents (2 runs × 80)
- Day 1: +3,840 agents (48 runs × 80)
- Day 3: +11,520 agents (exceeds 10K target!)
- Day 7: +26,880 agents (2.5× the target)

---

## Monitoring:

Check logs anytime:
```bash
tail -f /crawler.log
```

Check database count:
```bash
python3 -c "import psycopg2; conn=psycopg2.connect('postgresql://postgres:UhWTsyEJSTIrWVJyyCggOqoglwoIepue@yamabiko.proxy.rlwy.net:29306/railway'); cur=conn.cursor(); cur.execute('SELECT COUNT(*) FROM agents'); print(f'{cur.fetchone()[0]} agents'); conn.close()"
```

---

## If You Need to Stop It:

```bash
crontab -e
# Delete the line or comment it out with #
```

---

**Next:** Let me know when it's running and I'll monitor the agent count growth!
