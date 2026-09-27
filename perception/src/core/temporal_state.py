from __future__ import annotations

from dataclasses import dataclass
from collections import defaultdict
import time


@dataclass
class TrackState:
    key: str
    first_seen: float
    last_seen: float
    consecutive_hits: int = 0
    consecutive_misses: int = 0
    max_confidence: float = 0.0
    confirmed: bool = False


class TemporalStateManager:
    """
    Maintains temporal confirmation for detections.

    A detection becomes confirmed only after enough consecutive observations.
    It is cleared only after enough consecutive misses.
    """

    def __init__(
        self,
        confirm_hits: int = 3,
        clear_misses: int = 5,
        expiry_seconds: float = 10.0,
    ):
        self.confirm_hits = max(1, confirm_hits)
        self.clear_misses = max(1, clear_misses)
        self.expiry_seconds = max(1.0, expiry_seconds)
        self.states: dict[str, TrackState] = {}

    def update(
        self,
        key: str,
        detected: bool,
        confidence: float = 0.0,
        now: float | None = None,
    ) -> TrackState:

        now = now or time.time()

        state = self.states.get(key)

        if state is None:
            state = TrackState(
                key=key,
                first_seen=now,
                last_seen=now,
            )
            self.states[key] = state

        if detected:
            state.last_seen = now
            state.consecutive_hits += 1
            state.consecutive_misses = 0
            state.max_confidence = max(
                state.max_confidence,
                float(confidence),
            )

            if state.consecutive_hits >= self.confirm_hits:
                state.confirmed = True

        else:
            state.consecutive_misses += 1
            state.consecutive_hits = 0

            if state.consecutive_misses >= self.clear_misses:
                state.confirmed = False

        self.cleanup(now)

        return state

    def is_confirmed(self, key: str) -> bool:
        state = self.states.get(key)
        return bool(state and state.confirmed)

    def cleanup(self, now: float | None = None) -> None:
        now = now or time.time()

        expired = [
            key
            for key, state in self.states.items()
            if now - state.last_seen > self.expiry_seconds
        ]

        for key in expired:
            del self.states[key]

    def snapshot(self) -> dict:
        return {
            key: {
                "first_seen": state.first_seen,
                "last_seen": state.last_seen,
                "consecutive_hits": state.consecutive_hits,
                "consecutive_misses": state.consecutive_misses,
                "max_confidence": state.max_confidence,
                "confirmed": state.confirmed,
            }
            for key, state in self.states.items()
        }
