@echo off
title PERIMETER W - Backend + Frontend
echo ================================================
echo       PERIMETER W - LOCAL STARTER
echo ================================================
echo.
echo Starting FastAPI backend on http://127.0.0.1:8000 ...
start "PERIMETER BACKEND - DO NOT CLOSE" cmd /k "cd /d %~dp0backend && python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
timeout /t 2 /nobreak >nul
echo Starting frontend on http://localhost:8080 ...
start "PERIMETER FRONTEND - DO NOT CLOSE" cmd /k "cd /d %~dp0 && python serve.py"
timeout /t 3 /nobreak >nul
start "" "http://localhost:8080/register.html"
echo.
echo Both servers are starting in separate windows.
echo Keep both windows open while testing.
pause
