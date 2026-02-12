@echo off
echo Starting Agent Directory Exchange - Slow Crawler
echo This will run continuously in the background
echo Adding 10-20 agents every 2 hours
echo.
echo Press Ctrl+C to stop
echo.

start /min cmd /c "C:\Users\ADMIN\.openclaw\workspace\agentdirectory.exchange\crawler_automation.bat"

echo Crawler started in background!
echo Check agentdirectory.exchange for new agents every 2 hours
pause
