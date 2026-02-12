@echo off
REM Aggressive Crawler V2 - Deploy 785+ Agents
REM This deploys the aggressive discovery results (785 agents found)

echo ============================================================
echo AGGRESSIVE CRAWLER V2 - DEPLOYMENT
echo ============================================================
echo.
echo Found: 785 high-quality agents
echo Sources: HuggingFace (810) + GitHub (300)
echo Quality threshold: 40/100
echo.

REM Check file exists
if not exist "discovered_agents_v2.jsonl" (
    echo [ERROR] discovered_agents_v2.jsonl not found
    echo Running aggressive discovery...
    python agent_discovery_crawler_v2_aggressive.py
    echo.
)

REM Get DATABASE_URL
if "%DATABASE_URL%"=="" (
    echo [INFO] DATABASE_URL not set
    echo.
    echo Get from Railway:
    echo 1. https://railway.app/project/[your-project]
    echo 2. PostgreSQL → Variables → DATABASE_URL
    echo.
    set /p DATABASE_URL="Paste DATABASE_URL: "
)

echo.
echo [INFO] Installing dependencies...
pip install psycopg2-binary --quiet

echo.
echo [INFO] Deploying 785 agents to production...
echo [INFO] Using discovered_agents_v2.jsonl
python deploy_crawler_production.py "%DATABASE_URL%"

echo.
echo ============================================================
echo DEPLOYMENT COMPLETE
echo ============================================================
echo.
echo Expected results:
echo - 785+ agents listed on site
echo - Stats showing thousands of combinations
echo - Platform becomes largest agent directory
echo.
echo Next steps:
echo 1. Visit https://agentdirectory.exchange
echo 2. Verify agents are listed
echo 3. Set up hourly cron for continuous discovery
echo.
pause
