from __future__ import annotations

import json
from pathlib import Path


def read_replay(path="recordings/replay.jsonl"):
    file_path = Path(path)

    if not file_path.exists():
        return

    with file_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        for line in file:
            line = line.strip()

            if not line:
                continue

            yield json.loads(line)
