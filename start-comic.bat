@echo off
title ComicMn2
cd /d "%~dp0"

rem Open browser once frontend is up (runs in background)
start "" /min powershell -NoProfile -WindowStyle Hidden -Command "for($i=0;$i -lt 60;$i++){try{Invoke-WebRequest http://localhost:5173 -UseBasicParsing -TimeoutSec 1 | Out-Null; Start-Process http://localhost:5173; break}catch{Start-Sleep 1}}"

rem Backend + frontend in one window. Close window to stop all.
npx concurrently -n api,web -c blue,green "npm run backend" "npm run frontend"
pause
