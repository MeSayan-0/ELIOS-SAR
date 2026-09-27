from __future__ import annotations

from typing import Any
import time
import uuid


def build_event(
    event_type: str,
    payload: dict[str, Any],
    source: str = "onboard_ai",
    severity: str = "info",
) -> dict[str, Any]:

    return {
        "event_id": str(uuid.uuid4()),
        "event_type": event_type,
        "source": source,
        "severity": severity,
        "timestamp": time.time(),
        "payload": payload,
    }
