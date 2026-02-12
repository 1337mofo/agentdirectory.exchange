@echo off
REM Agent Directory Exchange - Continuous Slow Crawler
REM Runs every 2 hours, adds 10-20 agents per batch

echo [%date% %time%] Starting slow agent crawler...

cd C:\Users\ADMIN\.openclaw\workspace\agentdirectory.exchange

REM Run crawler (limit to 20 agents per run)
python deploy_crawler_production.py --limit 20 --quality-threshold 40

echo [%date% %time%] Crawler batch complete.
echo Sleeping for 2 hours...
timeout /t 7200 /nobreak

REM Loop forever
goto :loop
