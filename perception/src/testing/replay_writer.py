from __future__ import annotations

import json
from pathlib import Path
import time


class ReplayWriter:
    def __init__(
        self,
        path="recordings/replay.jsonl",
    ):
        self.path = Path(path)
        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    def write(self, frame_id, result):
        record = {
            "timestamp": time.time(),
            "frame_id": frame_id,
            "result": result,
        }

        with self.path.open(
            "a",
            encoding="utf-8",
        ) as file:
            file.write(
                json.dumps(
                    record,
                    default=str,
                )
                + "\n"
            )
