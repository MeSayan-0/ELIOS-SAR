from __future__ import annotations

import json
import logging
from pathlib import Path
from datetime import datetime, timezone


def configure_logging(
    name: str = "elios_sar",
    log_directory: str = "logs",
) -> logging.Logger:

    Path(log_directory).mkdir(
        parents=True,
        exist_ok=True,
    )

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    console = logging.StreamHandler()
    console.setFormatter(formatter)

    file_handler = logging.FileHandler(
        Path(log_directory) / "system.log",
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(console)
    logger.addHandler(file_handler)

    return logger


def write_event(
    event_type: str,
    payload: dict,
    directory: str = "logs",
) -> None:

    Path(directory).mkdir(
        parents=True,
        exist_ok=True,
    )

    record = {
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat(),
        "event_type": event_type,
        "payload": payload,
    }

    path = Path(directory) / "events.jsonl"

    with path.open(
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
