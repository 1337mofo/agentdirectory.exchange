# SSL Certificate Fix - Step-by-Step Instructions

## What You're Fixing
NET::ERR_CERT_COMMON_NAME_INVALID - Railway's SSL certificate not matching agentdirectory.exchange

## Step-by-Step (5 Minutes)

### 1. Login to Railway
- Go to: https://railway.app
- Login with your account
- Open project: **agentdirectoryexchange**

### 2. Navigate to Settings
- Click on the **web service** (not the database)
- Click **"Settings"** tab at top

### 3. Find Domains Section
- Scroll down to **"Domains"** section
- You should see:
  - ✅ `agentdirectoryexchange-production.up.railway.app` (Railway domain)
  - ⚠️ `agentdirectory.exchange` (custom domain - this is the problem)

### 4. Remove and Re-add Custom Domain
**Remove:**
- Find `agentdirectory.exchange` in the list
- Click the **trash icon** or **"Remove"** button
- Confirm removal

**Re-add:**
- Click **"+ Custom Domain"** button
- Enter: `agentdirectory.exchange`
- Railway will auto-provision new SSL certificate
- Wait message: "Provisioning SSL certificate..."

### 5. Wait for Provisioning (5-10 Minutes)
- Railway status will show: "Provisioning SSL certificate"
- Then: "Certificate issued"
- DNS is already correct (you did this yesterday)
- Just need new certificate binding

### 6. Verify Fix
After certificate issued:
- Open browser: https://agentdirectory.exchange/health
- Should see: `{"status": "healthy"}`
- Check for green padlock (no error)

## If Still Fails After 10 Minutes

### Check DNS Records
- Domain registrar: Verify CNAME record
- Should be: `agentdirectory.exchange` → `agentdirectoryexchange-production.up.railway.app`
- NO A records, NO AAAA records (only CNAME)

### Alternative: Use Railway URL Temporarily
- https://agentdirectoryexchange-production.up.railway.app
- Has valid SSL certificate
- All endpoints work
- Use this while fixing custom domain

## What Railway Is Doing Behind the Scenes
1. Detects custom domain added
2. Requests Let's Encrypt SSL certificate
3. Validates domain ownership via DNS
4. Issues certificate
5. Binds certificate to Railway service

## Current Status
- **DNS:** ✅ Working (domain resolves)
- **Backend:** ✅ Running (API responds)
- **SSL:** ❌ Certificate mismatch (fixing now)
- **Database:** ❌ Still needs DATABASE_URL (next priority)

## After SSL Fix
Next immediate priority: Fix DATABASE_URL so agent creation works.
