from __future__ import annotations

import csv
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict


@dataclass
class AttendanceStore:
    output_file: str
    min_seconds_between_marks: int = 60
    _last_marked: Dict[str, datetime] = field(default_factory=dict)

    def mark(self, name: str) -> bool:
        now = datetime.now()
        last_seen = self._last_marked.get(name)
        if last_seen and (now - last_seen).total_seconds() < self.min_seconds_between_marks:
            return False

        new_file = not os.path.exists(self.output_file)
        with open(self.output_file, "a", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            if new_file:
                writer.writerow(["name", "timestamp"])
            writer.writerow([name, now.isoformat(timespec="seconds")])

        self._last_marked[name] = now
        return True
