# Railway PostgreSQL Database Setup
**Agent Directory Exchange - Production Database**

---

## Current Status

**Railway Project:** agentdirectoryexchange (df459949-3d36-4601-afcc-e50869c28223)  
**PostgreSQL:** Should be provisioned already  
**Issue:** Local .env has localhost URL, need production URL  

---

## Step 1: Get Database URL from Railway

### Option A: Via Dashboard (Easy)
1. Go to https://railway.app/
2. Login with nova@theaerie.ai
3. Click **agentdirectoryexchange** project
4. Click **Postgres** service
5. Click **Variables** tab
6. Copy value of `DATABASE_URL`

**Format will be:**
```
postgresql://postgres:password@hostname:5432/railway
```

### Option B: Via Railway CLI
```bash
railway login
railway link
railway variables
```

Look for `DATABASE_URL` in output.

---

## Step 2: Update Backend .env

Replace this line in `backend/.env`:
```
DATABASE_URL=postgresql://user:password@localhost:5432/agent_marketplace
```

With Railway's actual URL:
```
DATABASE_URL=postgresql://postgres:ACTUAL_PASSWORD@ACTUAL_HOST.railway.app:5432/railway
```

---

## Step 3: Run Database Migrations

Once DATABASE_URL is set:

```bash
cd backend
python -c "from database.base import init_db; init_db()"
```

This creates all tables:
- agents
- listings  
- transactions
- agent_categories (when we migrate)

---

## Step 4: Deploy 785 Agents

With correct DATABASE_URL in environment:

```bash
cd C:\Users\ADMIN\.openclaw\workspace\agentdirectory.exchange
python deploy_crawler_production.py
```

Will insert 785 agents directly to production database.

---

## Step 5: Verify It Worked

Check via Railway dashboard:
1. Go to Postgres service
2. Click **Data** tab
3. Run query:
```sql
SELECT COUNT(*) FROM agents;
```

Should show 785+ agents.

Or check via API:
```bash
curl https://agentdirectory.exchange/api/v1/agents?limit=1
```

---

## Alternative: Use Railway's Environment Variables

Instead of storing DATABASE_URL locally, Railway can inject it:

### In `railway.json`:
```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/api/v1/stats"
  }
}
```

Railway automatically provides `DATABASE_URL` to the app.

---

## Security Best Practices

### ❌ Don't:
- Commit DATABASE_URL to git
- Share database password in messages
- Use same credentials for dev and prod

### ✅ Do:
- Use Railway's built-in secrets management
- Access DATABASE_URL via environment variables only
- Rotate passwords periodically

---

## What I Need to Deploy Agents:

**Option 1 (Secure):** 
- You copy DATABASE_URL from Railway
- Paste it into `backend/.env` locally
- I run deploy script
- We commit .env to .gitignore (never push it)

**Option 2 (More Secure):**
- Set DATABASE_URL as environment variable in Windows
- I access via `os.getenv("DATABASE_URL")`
- Never stored in file

**Option 3 (Most Secure - Steve does it):**
- You run deploy script yourself
- Your local environment has DATABASE_URL
- Agents deploy to production
- I never see the credentials

---

## Quick Command Reference

### Get DATABASE_URL:
```bash
# Via Railway dashboard
1. Login to railway.app
2. Project → Postgres → Variables → DATABASE_URL

# Via Railway CLI
railway variables | grep DATABASE_URL
```

### Test Connection:
```bash
# Python test
python -c "import psycopg2; conn = psycopg2.connect('YOUR_DATABASE_URL'); print('✅ Connected'); conn.close()"
```

### Deploy Agents:
```bash
# After DATABASE_URL is set
python deploy_crawler_production.py
```

---

## Current Blockers

1. **Missing production DATABASE_URL** - need it from Railway
2. **Local .env has localhost** - needs to be updated
3. **785 agents ready to deploy** - waiting for database connection

---

## Next Steps

**Steve action:**
1. Get DATABASE_URL from Railway dashboard
2. Either:
   - A) Give it to Nova (I'll deploy agents)
   - B) Set it locally and run deploy yourself
   - C) Set as Windows environment variable

**Once DATABASE_URL is correct:**
- ✅ Deploy 785 agents (2 minutes)
- ✅ Site will show real agent count
- ✅ Can start building transaction features

---

**Status:** Waiting for production DATABASE_URL to proceed.
