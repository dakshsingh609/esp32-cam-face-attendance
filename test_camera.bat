@echo off
cd /d "%~dp0"
set "IP="

if exist esp32_ip.txt (
  for /f "usebackq delims=" %%a in ("esp32_ip.txt") do set "IP=%%a"
)

if "%IP%"=="" (
  echo.
  echo Paste ESP32 IP from Serial Monitor ^(example: 192.168.1.13^)
  set /p "IP=IP: "
)

echo.
echo Step A - open home page:
echo   http://%IP%/
echo Step B - open camera photo:
echo   http://%IP%/capture
echo.
echo If Step A fails: ESP32 is offline or wrong IP. Check Serial Monitor.
echo If Step A works but B fails: re-upload esp32_cam_attendance.ino in Arduino.
echo.

start "" "http://%IP%/"
timeout /t 2 /nobreak >nul
start "" "http://%IP%/capture"
pause
