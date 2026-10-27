@echo off
cd /d "%~dp0"
set IP=

if exist esp32_ip.txt (
  for /f "usebackq delims=" %%a in ("esp32_ip.txt") do set "IP=%%a"
)

if "%IP%"=="" (
  echo.
  echo Paste your ESP32 IP from Arduino Serial Monitor ^(example: 192.168.1.45^)
  set /p IP=IP: 
)

if not exist .venv\Scripts\python.exe (
  echo Creating virtual environment...
  python -m venv .venv
  call .venv\Scripts\activate.bat
  pip install -r requirements.txt
) else (
  call .venv\Scripts\activate.bat
)

echo Starting attendance with ESP32 at %IP%
python -m app.main --esp32-ip %IP%
pause
