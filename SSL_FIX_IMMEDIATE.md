# SSL Certificate Fix - IMMEDIATE

## Problem
NET::ERR_CERT_COMMON_NAME_INVALID error at https://agentdirectory.exchange

## Root Cause
Railway's SSL certificate not properly bound to custom domain. DNS is correct (site resolves) but certificate validation failing.

## Fix Steps (Railway Dashboard)

### Option 1: Re-provision Certificate
1. Go to Railway project: agentdirectoryexchange
2. Click "Settings" tab
3. Scroll to "Domains" section
4. Find agentdirectory.exchange
5. Click "Remove" then "Add Domain" again
6. Railway will re-provision SSL certificate (5-10 minutes)

### Option 2: Check Domain Configuration
1. Verify CNAME record points to Railway: `agentdirectoryexchange-production.up.railway.app`
2. Check for conflicting A/AAAA records (should only be CNAME)
3. Clear any CloudFlare/proxy settings if domain uses them

### Option 3: Force HTTPS Settings
1. Railway Settings → Environment Variables
2. Check if `FORCE_SSL=true` is set
3. Verify PORT is set to Railway's internal port

## Verification
After fix, test:
- https://agentdirectory.exchange/health
- https://agentdirectory.exchange/docs
- Check browser shows green padlock (valid certificate)

## Timeline
- Certificate re-provisioning: 5-10 minutes
- DNS cache clear: Up to 1 hour
- If still failing after 1 hour: Contact Railway support

## Current Status
- DNS: ✅ Working (domain resolves)
- SSL: ❌ Certificate mismatch
- Backend: ✅ Running (Railway URL works)
- Database: ❌ Still needs DATABASE_URL fix

## Workaround (Temporary)
Use Railway URL directly: https://agentdirectoryexchange-production.up.railway.app
- Has valid Railway SSL certificate
- All API endpoints work
- Use until custom domain SSL fixed
