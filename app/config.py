from __future__ import annotations

import argparse
import os
from dataclasses import dataclass


def _normalize_base_url(value: str) -> str:
    raw = value.strip().rstrip("/")
    if raw.startswith("http://") or raw.startswith("https://"):
        return raw
    return f"http://{raw}"


@dataclass(frozen=True)
class AppConfig:
    esp32_base_url: str
    stream_path: str = "/stream"
    capture_path: str = "/capture"
    camera_timeout_s: float = 10.0
    reconnect_delay_s: float = 1.5
    reconnect_backoff_max_s: float = 10.0
    frame_queue_size: int = 4
    face_match_threshold: float = 0.48
    min_seconds_between_marks: int = 60
    known_faces_dir: str = "known_faces"
    attendance_file: str = "attendance.csv"

    @property
    def stream_url(self) -> str:
        return f"{self.esp32_base_url}{self.stream_path}"

    @property
    def capture_url(self) -> str:
        return f"{self.esp32_base_url}{self.capture_path}"


def from_args() -> AppConfig:
    parser = argparse.ArgumentParser(description="ESP32-CAM facial attendance")
    parser.add_argument("--esp32-ip", default=os.getenv("ESP32_IP", "192.168.1.200"))
    parser.add_argument("--stream-path", default=os.getenv("ESP32_STREAM_PATH", "/stream"))
    parser.add_argument("--capture-path", default=os.getenv("ESP32_CAPTURE_PATH", "/capture"))
    parser.add_argument("--camera-timeout", type=float, default=float(os.getenv("CAMERA_TIMEOUT_S", "10")))
    parser.add_argument("--reconnect-delay", type=float, default=float(os.getenv("RECONNECT_DELAY_S", "1.5")))
    parser.add_argument("--reconnect-max", type=float, default=float(os.getenv("RECONNECT_BACKOFF_MAX_S", "10")))
    parser.add_argument("--frame-queue-size", type=int, default=int(os.getenv("FRAME_QUEUE_SIZE", "4")))
    parser.add_argument("--threshold", type=float, default=float(os.getenv("FACE_MATCH_THRESHOLD", "0.48")))
    parser.add_argument("--min-mark-seconds", type=int, default=int(os.getenv("MIN_SECONDS_BETWEEN_MARKS", "60")))
    parser.add_argument("--known-faces-dir", default=os.getenv("KNOWN_FACES_DIR", "known_faces"))
    parser.add_argument("--attendance-file", default=os.getenv("ATTENDANCE_FILE", "attendance.csv"))
    args = parser.parse_args()

    return AppConfig(
        esp32_base_url=_normalize_base_url(args.esp32_ip),
        stream_path=args.stream_path if args.stream_path.startswith("/") else f"/{args.stream_path}",
        capture_path=args.capture_path if args.capture_path.startswith("/") else f"/{args.capture_path}",
        camera_timeout_s=max(2.0, args.camera_timeout),
        reconnect_delay_s=max(0.5, args.reconnect_delay),
        reconnect_backoff_max_s=max(args.reconnect_delay, args.reconnect_max),
        frame_queue_size=max(1, args.frame_queue_size),
        face_match_threshold=max(0.2, min(0.7, args.threshold)),
        min_seconds_between_marks=max(1, args.min_mark_seconds),
        known_faces_dir=args.known_faces_dir,
        attendance_file=args.attendance_file,
    )
