# Facial Attendance with ESP32-CAM

End-to-end starter project for a facial-recognition attendance system using:
- ESP32-CAM (AI Thinker) as camera streamer
- Python app on PC for recognition + attendance CSV marking

## Project structure

```text
facial-attendance-esp32/
├─ app/
│  ├─ __init__.py
│  ├─ attendance.py
│  ├─ config.py
│  ├─ esp32_stream.py
│  └─ main.py
├─ esp32/
│  ├─ esp32_cam_attendance/
│  │  ├─ esp32_cam_attendance.ino
│  │  └─ wifi_config.h          (local only; copy from example)
│  └─ wifi_config.example.h
├─ .gitignore
├─ requirements.txt
└─ README.md
```

## 1) ESP32 firmware setup (AI Thinker)

1. Install Arduino IDE (or PlatformIO) with ESP32 board support.
2. Open `esp32/esp32_cam_attendance/esp32_cam_attendance.ino`.
3. In the **same folder as the `.ino`**, copy:
   - `esp32/wifi_config.example.h` -> `esp32/esp32_cam_attendance/wifi_config.h`
4. Edit `wifi_config.h` with your real SSID/password (Arduino only searches the sketch folder for `#include "wifi_config.h"`).
5. Select board **AI Thinker ESP32-CAM** and correct COM port.
6. Upload firmware.
7. Open Serial Monitor at 115200 and note ESP32 IP.

### Firmware endpoints

- `GET /stream` -> MJPEG stream for live recognition
- `GET /capture` -> single JPEG frame (quick network/camera test)
- `GET /` -> simple health text

## 2) Python app setup (PC)

### Prerequisites
- Python 3.10+ recommended
- Webcam not required (uses ESP32 stream)

### Install

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
# source .venv/bin/activate

pip install -r requirements.txt
```

### Add known faces

Create `known_faces/` in project root and add one clear face image per person:
- `Alice.jpg`
- `Bob.png`

File name (without extension) is used as attendance name.

### Run app

```bash
python -m app.main --esp32-ip 192.168.1.200
```

You can also pass full URL:

```bash
python -m app.main --esp32-ip http://192.168.1.200
```

Press `q` on the video window to exit gracefully.

## Config and reliability options

All options are configurable via CLI flags or environment variables:

- `--esp32-ip` / `ESP32_IP`
- `--stream-path` / `ESP32_STREAM_PATH` (default `/stream`)
- `--capture-path` / `ESP32_CAPTURE_PATH` (default `/capture`)
- `--camera-timeout` / `CAMERA_TIMEOUT_S`
- `--reconnect-delay` / `RECONNECT_DELAY_S`
- `--reconnect-max` / `RECONNECT_BACKOFF_MAX_S`
- `--frame-queue-size` / `FRAME_QUEUE_SIZE`
- `--threshold` / `FACE_MATCH_THRESHOLD` (lower = stricter)
- `--min-mark-seconds` / `MIN_SECONDS_BETWEEN_MARKS`
- `--known-faces-dir` / `KNOWN_FACES_DIR`
- `--attendance-file` / `ATTENDANCE_FILE`

Implemented reliability features:
- robust URL normalization (`IP` or `http://IP`)
- stream reconnect with exponential backoff
- request timeouts
- bounded frame queue with drop-oldest policy (low latency)
- graceful shutdown on `q`, `Ctrl+C`, or termination signal
- unknown-face handling with configurable threshold
- attendance de-dup window to avoid repeated rapid marks

## Output

- Attendance file: `attendance.csv`
- Format: `name,timestamp`

## Security and secrets

- Do **not** commit `esp32/esp32_cam_attendance/wifi_config.h` (or `esp32/wifi_config.h`) — they contain WiFi credentials.
- Commit only `esp32/wifi_config.example.h` template.

## Quick test flow

1. Confirm ESP32 online in browser:
   - `http://<ESP32_IP>/`
   - `http://<ESP32_IP>/capture`
2. Run:
   - `python -m app.main --esp32-ip <ESP32_IP>`
3. Show face of known person.
4. Verify new row appears in `attendance.csv`.
