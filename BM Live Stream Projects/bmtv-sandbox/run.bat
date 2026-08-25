@echo off
REM Double-click to start the BMB Sandbox Server.
cd /d "%~dp0"
where python >nul 2>nul || (echo Python not found. Install Python 3 from python.org & pause & exit /b)
echo Starting BMB Sandbox Server...
start "" http://127.0.0.1:8790/
python serve.py
pause
