# Railway Deployment Diagnosis

**Issue:** App timing out with 502 Bad Gateway

**Time:** 2026-02-12 19:12 GMT+7

---

## What We Know

1. ✅ Code pushed successfully (commit eadc79a)
2. ✅ Syntax is valid (compiled without errors)
3. ❌ App not responding after 10+ minutes
4. ❌ Request times out after 10 seconds

---

## Possible Causes

### 1. Railway Build Failed
- Docker build error
- Missing dependency
- Build logs will show error

### 2. App Crashes on Startup
- Import error
- Database connection failing
- Environment variable missing

### 3. App Starts But Hangs
- Database initialization blocking
- Infinite loop somewhere
- Waiting for external service

### 4. Railway Still Building
- Complex builds can take 5-10 minutes
- Check deployment status

---

## How to Diagnose (Railway Dashboard)

1. **Go to Railway Project**
   - https://railway.com/project/df459949-3d36-4601-afcc-e50869c28223

2. **Check Deployment Status**
   - Click "agentdirectory.exchange" service
   - Click "Deployments" tab
   - Look for commit eadc79a
   - Status should be "Active" (not "Building" or "Failed")

3. **View Logs**
   - Click deployment → "View Logs"
   - Look for:
     - "Application startup complete" (good)
     - Import errors (bad)
     - Database connection errors (bad)
     - Traceback messages (bad)

4. **Check Environment Variables**
   - Click "Variables" tab
   - Verify DATABASE_URL is set
   - Verify PORT is available (Railway sets this)

---

## Quick Tests

### Test 1: Health Endpoint
```
curl https://agentdirectory.exchange/health
```

Should return: `{"status":"healthy"}`

If this works, app is running but root path has issues.

### Test 2: API Docs
```
curl https://agentdirectory.exchange/docs
```

Should return HTML page.

If this works, app is running and FastAPI is operational.

### Test 3: Stats Endpoint
```
curl https://agentdirectory.exchange/api/v1/stats
```

Should return JSON with agent count.

---

## Common Errors & Solutions

### Error: "Module not found"
**Cause:** Missing dependency in requirements.txt  
**Fix:** Add missing package, push, redeploy

### Error: "Database connection refused"
**Cause:** DATABASE_URL incorrect or PostgreSQL not running  
**Fix:** Verify DATABASE_URL in Railway variables

### Error: "Port already in use"
**Cause:** Railway's PORT env var not being used  
**Fix:** Ensure using `--port $PORT` in start command

### Error: "Import cycle"
**Cause:** Circular imports in Python code  
**Fix:** Reorganize imports

---

## Nuclear Option: Minimal Test

If all else fails, create a minimal app that ONLY serves root:

```python
# minimal_test.py
from fastapi import FastAPI
app = FastAPI()

@app.get("/")
def root():
    return {"status": "minimal app working"}

@app.get("/health")
def health():
    return {"status": "healthy"}
```

Update railway.json:
```json
"startCommand": "python -m uvicorn minimal_test:app --host 0.0.0.0 --port $PORT"
```

If this works, problem is in main.py complexity.  
If this fails, problem is Railway configuration.

---

## Next Steps

1. Check Railway deployment logs (CRITICAL)
2. Test /health endpoint
3. If health works, problem is specific to root path
4. If health fails, problem is app startup
5. Share logs with Nova for diagnosis
