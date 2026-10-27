from __future__ import annotations

import logging
import os
import signal
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

import cv2
import face_recognition
import numpy as np
import requests

from .attendance import AttendanceStore
from .config import AppConfig, from_args
from .esp32_stream import Esp32StreamClient, StreamConfig


LOG = logging.getLogger("facial_attendance")


@dataclass(frozen=True)
class KnownFaces:
    names: List[str]
    encodings: List[np.ndarray]


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


def load_known_faces(known_faces_dir: str) -> KnownFaces:
    names: List[str] = []
    encodings: List[np.ndarray] = []
    path = Path(known_faces_dir)
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        LOG.warning("Known faces folder created at %s. Add person images first.", known_faces_dir)
        return KnownFaces(names, encodings)

    image_exts = {".jpg", ".jpeg", ".png"}
    for image_path in sorted(path.iterdir()):
        if image_path.suffix.lower() not in image_exts:
            continue
        image = face_recognition.load_image_file(str(image_path))
        face_vectors = face_recognition.face_encodings(image)
        if not face_vectors:
            LOG.warning("No face found in %s", image_path.name)
            continue
        names.append(image_path.stem)
        encodings.append(face_vectors[0])

    LOG.info("Loaded %d known faces", len(names))
    return KnownFaces(names, encodings)


def label_face(
    face_encoding: np.ndarray,
    known: KnownFaces,
    threshold: float,
) -> Tuple[str, float]:
    if not known.encodings:
        return "Unknown", 1.0

    distances = face_recognition.face_distance(known.encodings, face_encoding)
    best_idx = int(np.argmin(distances))
    best_distance = float(distances[best_idx])
    if best_distance <= threshold:
        return known.names[best_idx], best_distance
    return "Unknown", best_distance


def test_capture_endpoint(cfg: AppConfig) -> None:
    try:
        response = requests.get(cfg.capture_url, timeout=cfg.camera_timeout_s)
        response.raise_for_status()
        LOG.info("Capture endpoint OK (%d bytes)", len(response.content))
    except Exception as exc:  # noqa: BLE001
        LOG.warning("Capture endpoint check failed: %s", exc)


def run(cfg: AppConfig) -> int:
    known = load_known_faces(cfg.known_faces_dir)
    attendance = AttendanceStore(
        output_file=cfg.attendance_file,
        min_seconds_between_marks=cfg.min_seconds_between_marks,
    )

    stream_client = Esp32StreamClient(
        StreamConfig(
            stream_url=cfg.stream_url,
            timeout_s=cfg.camera_timeout_s,
            reconnect_delay_s=cfg.reconnect_delay_s,
            reconnect_backoff_max_s=cfg.reconnect_backoff_max_s,
            frame_queue_size=cfg.frame_queue_size,
        )
    )
    stream_client.start()
    test_capture_endpoint(cfg)

    stop = False

    def handle_signal(_sig: int, _frame: object) -> None:
        nonlocal stop
        stop = True

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    try:
        while not stop:
            frame = stream_client.get_frame(timeout_s=1.0)
            if frame is None:
                continue

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            locations = face_recognition.face_locations(rgb, model="hog")
            encs = face_recognition.face_encodings(rgb, locations)

            for (top, right, bottom, left), enc in zip(locations, encs):
                name, distance = label_face(enc, known, cfg.face_match_threshold)
                if name != "Unknown":
                    marked = attendance.mark(name)
                    if marked:
                        LOG.info("Marked attendance: %s (distance=%.3f)", name, distance)

                color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                cv2.putText(
                    frame,
                    f"{name} ({distance:.2f})",
                    (left, max(20, top - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    color,
                    2,
                )

            cv2.imshow("ESP32 Facial Attendance", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        stream_client.stop()
        cv2.destroyAllWindows()
    return 0


def ensure_dirs(cfg: AppConfig) -> None:
    os.makedirs(cfg.known_faces_dir, exist_ok=True)
    attendance_parent = os.path.dirname(cfg.attendance_file)
    if attendance_parent:
        os.makedirs(attendance_parent, exist_ok=True)


def main() -> int:
    setup_logging()
    cfg = from_args()
    LOG.info("ESP32 stream URL: %s", cfg.stream_url)
    ensure_dirs(cfg)
    return run(cfg)


if __name__ == "__main__":
    sys.exit(main())
