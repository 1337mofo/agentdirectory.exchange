# Agent Directory Exchange - Post-Deployment Setup

## ✅ Deployment Complete (2026-02-12 12:27 GMT+7)

Railway successfully built and deployed using Dockerfile approach.

## Step 1: Verify Deployment (NOW)

**Get the Railway URL:**
1. In Railway dashboard, click on the deployment
2. Copy the `.railway.app` URL (should be something like `web-production-xxxx.up.railway.app`)
3. Visit: `https://[your-url].railway.app/health`
4. Should return: `{"status": "healthy", "service": "Agent Directory Exchange"}`

## Step 2: Add PostgreSQL Database

**In Railway dashboard:**
1. Click "+ New" button
2. Select "Database" → "PostgreSQL"
3. Railway will automatically:
   - Create the database
   - Add `DATABASE_URL` environment variable
   - Link it to your web service
4. Deployment will auto-restart with database connected

## Step 3: Configure Environment Variables

**Add these in Railway → Variables tab:**

```env
# Database (auto-added by Railway when you create PostgreSQL)
DATABASE_URL=postgresql://...

# Stripe (for payment processing)
STRIPE_SECRET_KEY=sk_test_...  # Get from Stripe dashboard
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...  # Will get after webhook setup

# RapidAPI (for arbitrage fulfillment)
RAPIDAPI_KEY=your_rapidapi_key

# API Keys (optional - for development)
SECRET_KEY=generate_a_random_secret_key_here

# Environment
ENVIRONMENT=production
```

## Step 4: Setup Stripe Webhooks

**After deployment URL is confirmed:**

1. Go to Stripe Dashboard → Developers → Webhooks
2. Add endpoint: `https://agentdirectory.exchange/api/v1/webhooks/stripe`
3. Select events to send:
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
   - `charge.refunded`
4. Copy the webhook signing secret
5. Add to Railway environment variables as `STRIPE_WEBHOOK_SECRET`

## Step 5: Configure Custom Domain

**In Railway dashboard:**

1. Go to Settings → Domains
2. Click "Add Domain"
3. Enter: `agentdirectory.exchange`
4. Railway will show DNS records needed

**In Namecheap DNS settings:**

Copy the DNS records from Railway (will be something like):
```
Type: CNAME
Host: @
Value: [provided by Railway]
```

Or:
```
Type: A
Host: @
Value: [IP provided by Railway]
```

**DNS propagation takes 5-60 minutes.**

## Step 6: Test Complete Flow

Once domain is configured:

1. Visit `https://agentdirectory.exchange`
2. Check API docs: `https://agentdirectory.exchange/docs`
3. Test search: `https://agentdirectory.exchange/api/v1/agents/search?query=test`
4. Test payment flow (Stripe test mode)

## Step 7: Run Discovery Crawler

After everything is confirmed working:

```bash
python eagle-agent-marketplace/backend/services/agent_discovery_crawler.py
```

This will populate the marketplace with initial agent listings.

## Monitoring

**Railway provides:**
- Logs (real-time application logs)
- Metrics (CPU, memory, requests)
- Deploy history
- One-click rollbacks

**Access logs:** Railway dashboard → Logs tab

## Cost Tracking

**Current Railway costs:**
- Hobby plan: $5/month (includes PostgreSQL)
- Scales automatically with traffic
- No surprise charges (capped at plan limit)

## Rollback Plan

If something breaks:

1. Railway dashboard → Deployments tab
2. Find last working deployment
3. Click "Redeploy"
4. Instant rollback (< 30 seconds)

## Success Metrics

**Deployment is fully operational when:**
- ✅ /health endpoint returns 200 OK
- ✅ PostgreSQL connected (check logs for "Database connected")
- ✅ Custom domain resolves to Railway app
- ✅ Stripe webhooks receiving events
- ✅ /docs page loads (FastAPI auto-generated docs)

---

**Current Status:** Step 1 - Need Railway URL to proceed
**Next Action:** Copy `.railway.app` URL from Railway dashboard
