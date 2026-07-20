@echo off
REM Double-click to start the Loop Builder.
cd /d "%~dp0"
where python >nul 2>nul || (echo Python not found. Install Python 3 from python.org & pause & exit /b)
echo Installing/updating dependencies (first run only)...
python -m pip install -r requirements.txt --quiet
echo Starting ChannelCast Loop Builder...
start "" http://127.0.0.1:8765
python app.py
pause
