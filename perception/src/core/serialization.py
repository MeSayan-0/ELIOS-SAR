from __future__ import annotations

from dataclasses import is_dataclass, asdict
from enum import Enum
from typing import Any


def serialize(value: Any) -> Any:
    """
    Convert dataclasses, enums, lists and dictionaries into JSON-safe values.
    """

    if value is None:
        return None

    if is_dataclass(value):
        return serialize(asdict(value))

    if isinstance(value, Enum):
        return value.value

    if isinstance(value, dict):
        return {
            str(key): serialize(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple, set)):
        return [
            serialize(item)
            for item in value
        ]

    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass

    if hasattr(value, "tolist"):
        try:
            return value.tolist()
        except Exception:
            pass

    if isinstance(value, (str, int, float, bool)):
        return value

    return str(value)
