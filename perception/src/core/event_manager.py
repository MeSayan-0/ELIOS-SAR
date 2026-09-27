from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import hashlib
import json
import time


@dataclass
class EventRecord:
    event_key: str
    last_emitted: float
    count: int = 0
    last_payload: dict[str, Any] = field(default_factory=dict)


class EventManager:
    """
    Deduplicates and rate-limits repeated events.

    The same event will not be emitted repeatedly within cooldown_seconds.
    """

    def __init__(self, cooldown_seconds: float = 3.0):
        self.cooldown_seconds = max(0.0, cooldown_seconds)
        self.records: dict[str, EventRecord] = {}

    @staticmethod
    def make_key(
        event_type: str,
        identity: str,
        severity: str = "",
    ) -> str:
        raw = f"{event_type}|{identity}|{severity}"
        return hashlib.sha1(raw.encode()).hexdigest()[:16]

    def should_emit(
        self,
        event_type: str,
        identity: str,
        severity: str = "",
        now: float | None = None,
    ) -> bool:

        now = now or time.time()

        key = self.make_key(
            event_type,
            identity,
            severity,
        )

        record = self.records.get(key)

        if record is None:
            self.records[key] = EventRecord(
                event_key=key,
                last_emitted=now,
                count=1,
            )
            return True

        record.count += 1

        if now - record.last_emitted >= self.cooldown_seconds:
            record.last_emitted = now
            return True

        return False

    def record_payload(
        self,
        event_type: str,
        identity: str,
        payload: dict[str, Any],
        severity: str = "",
    ) -> None:

        key = self.make_key(
            event_type,
            identity,
            severity,
        )

        if key not in self.records:
            self.records[key] = EventRecord(
                event_key=key,
                last_emitted=time.time(),
            )

        self.records[key].last_payload = payload

    def clear(self) -> None:
        self.records.clear()

    def snapshot(self) -> dict:
        return {
            key: {
                "last_emitted": record.last_emitted,
                "count": record.count,
                "last_payload": record.last_payload,
            }
            for key, record in self.records.items()
        }
