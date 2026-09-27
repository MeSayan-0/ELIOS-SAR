from __future__ import annotations

import os
from pathlib import Path


def load_env_file(path: str = ".env.hardened") -> None:
    file_path = Path(path)

    if not file_path.exists():
        return

    for raw_line in file_path.read_text(
        encoding="utf-8"
    ).splitlines():

        line = raw_line.strip()

        if not line or line.startswith("#"):
            continue

        if "=" not in line:
            continue

        key, value = line.split("=", 1)

        key = key.strip()
        value = value.strip()

        os.environ.setdefault(key, value)


def env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except ValueError:
        return default


def env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except ValueError:
        return default


def env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)

    if value is None:
        return default

    return value.lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
