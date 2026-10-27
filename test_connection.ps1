$ip = (Get-Content "$PSScriptRoot\esp32_ip.txt" -ErrorAction SilentlyContinue | Select-Object -First 1).Trim()
if (-not $ip) {
    $ip = Read-Host "Enter ESP32 IP (example 192.168.1.13)"
}

Write-Host "`nTesting ESP32 at $ip ...`n"

try {
    $root = Invoke-WebRequest -Uri "http://$ip/" -TimeoutSec 8 -UseBasicParsing
    Write-Host "[OK] Home page:" $root.Content
} catch {
    Write-Host "[FAIL] Home page:" $_.Exception.Message
    Write-Host "Fix: power ESP32, check WiFi, confirm IP in Serial Monitor (115200)."
    Read-Host "Press Enter to exit"
    exit 1
}

try {
    $cap = Invoke-WebRequest -Uri "http://$ip/capture" -TimeoutSec 15 -UseBasicParsing
    Write-Host "[OK] Capture image bytes:" $cap.RawContentLength
    Start-Process "http://$ip/capture"
} catch {
    Write-Host "[FAIL] Capture:" $_.Exception.Message
    Write-Host "Fix: upload latest esp32_cam_attendance.ino from Arduino IDE, then RESET."
}

Read-Host "`nPress Enter to exit"
