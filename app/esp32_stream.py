from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from queue import Empty, Full, Queue
from typing import Optional

import cv2
import numpy as np
import requests


LOG = logging.getLogger(__name__)


@dataclass(frozen=True)
class StreamConfig:
    stream_url: str
    timeout_s: float = 10.0
    reconnect_delay_s: float = 1.5
    reconnect_backoff_max_s: float = 10.0
    frame_queue_size: int = 4


class Esp32StreamClient:
    def __init__(self, config: StreamConfig) -> None:
        self._cfg = config
        self._queue: Queue[np.ndarray] = Queue(maxsize=config.frame_queue_size)
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._session = requests.Session()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=3.0)
        self._session.close()

    def get_frame(self, timeout_s: float = 1.0) -> Optional[np.ndarray]:
        try:
            return self._queue.get(timeout=timeout_s)
        except Empty:
            return None

    def _enqueue_latest(self, frame: np.ndarray) -> None:
        if self._queue.full():
            try:
                self._queue.get_nowait()
            except Empty:
                pass
        try:
            self._queue.put_nowait(frame)
        except Full:
            pass

    def _run(self) -> None:
        backoff = self._cfg.reconnect_delay_s
        while not self._stop_event.is_set():
            try:
                self._consume_stream()
                backoff = self._cfg.reconnect_delay_s
            except Exception as exc:  # noqa: BLE001
                LOG.warning("Stream error (%s). Reconnecting in %.1fs", exc, backoff)
                if self._stop_event.wait(backoff):
                    break
                backoff = min(self._cfg.reconnect_backoff_max_s, backoff * 1.8)

    def _consume_stream(self) -> None:
        LOG.info("Connecting to stream: %s", self._cfg.stream_url)
        response = self._session.get(self._cfg.stream_url, stream=True, timeout=self._cfg.timeout_s)
        response.raise_for_status()

        boundary = b"\xff\xd8"
        trailer = b"\xff\xd9"
        buffer = b""

        for chunk in response.iter_content(chunk_size=2048):
            if self._stop_event.is_set():
                return
            if not chunk:
                continue
            buffer += chunk

            while True:
                start = buffer.find(boundary)
                if start < 0:
                    break
                end = buffer.find(trailer, start + 2)
                if end < 0:
                    break

                jpeg = buffer[start : end + 2]
                buffer = buffer[end + 2 :]

                image_array = np.frombuffer(jpeg, dtype=np.uint8)
                frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
                if frame is not None:
                    self._enqueue_latest(frame)
