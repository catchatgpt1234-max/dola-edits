@echo off
title Dola Edits AI - Live Cloudflare Server (dolaedits.online)
echo ========================================================
echo   Starting Dola Edits Server and Cloudflare Tunnel
echo   Your domain: https://dolaedits.online
echo ========================================================

start "Dola Edits Backend" python run.py
timeout /t 3 /nobreak >nul

echo.
echo [LIVE] Starting Cloudflare Tunnel for dolaedits.online...
echo Connected to: https://dolaedits.online
echo.
"C:\Program Files (x86)\cloudflared\cloudflared.exe" tunnel run dolaedits
pause
