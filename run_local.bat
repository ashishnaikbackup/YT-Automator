@echo off
setlocal
cd /d %~dp0

where python >nul 2>nul
if errorlevel 1 (
  echo Python 3 is required.
  pause
  exit /b 1
)

if not exist .venv (
  python -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install -r requirements.txt

where ollama >nul 2>nul
if errorlevel 1 (
  echo.
  echo Ollama is not installed. Install Ollama, then run this file again.
  echo https://ollama.com/
  pause
  exit /b 1
)

set LLM_PROVIDER=ollama
start "YT-Automator Server" cmd /k "call .venv\Scripts\activate.bat && set LLM_PROVIDER=ollama && python api.py"
timeout /t 3 /nobreak >nul
start http://127.0.0.1:5000
