from __future__ import annotations

from typing import Any, Callable

from src.core.event_builder import build_event
from src.core.event_manager import EventManager
from src.core.logging_utils import write_event


class SafeEventEmitter:
    def __init__(
        self,
        sender: Callable[[dict[str, Any]], None] | None = None,
        cooldown_seconds: float = 3.0,
    ):
        self.sender = sender
        self.manager = EventManager(
            cooldown_seconds=cooldown_seconds
        )

    def emit(
        self,
        event_type: str,
        identity: str | None = None,
        payload: dict[str, Any] | None = None,
        severity: str = "info",
        force: bool = False,
        **kwargs
    ) -> bool:

        if payload is None:
            payload = dict(kwargs)
        elif kwargs:
            payload = {**payload, **kwargs}

        if identity is None:
            identity = str(payload.get("identity", payload.get("track_id", event_type)))

        if not force:
            allowed = self.manager.should_emit(
                event_type=event_type,
                identity=identity,
                severity=severity,
            )

            if not allowed:
                return False

        event = build_event(
            event_type=event_type,
            payload=payload,
            severity=severity,
        )

        self.manager.record_payload(
            event_type=event_type,
            identity=identity,
            payload=payload,
            severity=severity,
        )

        write_event(
            event_type=event_type,
            payload=event,
        )

        if self.sender:
            try:
                self.sender(event)
            except Exception:
                pass

        return True
