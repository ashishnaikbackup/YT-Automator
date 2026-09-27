@echo off
cd /d %~dp0
where python >nul 2>nul || (echo Python is not installed or not on PATH.&pause&exit /b 1)
python -m pip install -r requirements.txt
if not exist outputs mkdir outputs
echo.
echo Starting YT-Automator at http://127.0.0.1:5000
python local_app.py
pause
