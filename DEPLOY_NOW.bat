@echo off
REM Agent Crawler - Deploy to Production
REM This script deploys discovered agents to Railway database

echo ============================================================
echo AGENT CRAWLER - PRODUCTION DEPLOYMENT
echo ============================================================
echo.

REM Check if discovered_agents.jsonl exists
if not exist "discovered_agents.jsonl" (
    echo [ERROR] discovered_agents.jsonl not found
    echo Running discovery first...
    python agent_discovery_crawler.py
    echo.
)

REM Prompt for DATABASE_URL if not set
if "%DATABASE_URL%"=="" (
    echo [INFO] DATABASE_URL not set in environment
    echo.
    echo Please get DATABASE_URL from Railway:
    echo 1. Go to https://railway.app/project/[your-project]
    echo 2. Click on PostgreSQL service
    echo 3. Click "Variables" tab
    echo 4. Copy DATABASE_URL value
    echo.
    set /p DATABASE_URL="Paste DATABASE_URL here: "
)

echo.
echo [INFO] Using DATABASE_URL: %DATABASE_URL:~0,30%...
echo.
echo [INFO] Installing required packages...
pip install psycopg2-binary --quiet

echo.
echo [INFO] Deploying agents to production database...
python deploy_crawler_production.py "%DATABASE_URL%"

echo.
echo ============================================================
echo DEPLOYMENT COMPLETE
echo ============================================================
echo.
echo Next steps:
echo 1. Visit https://agentdirectory.exchange
echo 2. Check agents are listed
echo 3. Set up cron job for continuous discovery
echo.
pause
