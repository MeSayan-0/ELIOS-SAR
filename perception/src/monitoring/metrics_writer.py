from __future__ import annotations

import json
from pathlib import Path
import time


class MetricsWriter:
    def __init__(
        self,
        path: str = "logs/metrics.jsonl",
    ):
        self.path = Path(path)
        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    def write(self, metrics: dict) -> None:
        record = {
            "timestamp": time.time(),
            **metrics,
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
