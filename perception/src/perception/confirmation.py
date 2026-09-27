from __future__ import annotations

from typing import Iterable

from src.core.temporal_state import TemporalStateManager


class DetectionConfirmation:
    """
    Converts noisy frame-level detections into confirmed observations.
    """

    def __init__(
        self,
        confirm_hits: int = 3,
        clear_misses: int = 5,
    ):
        self.manager = TemporalStateManager(
            confirm_hits=confirm_hits,
            clear_misses=clear_misses,
        )

    def process(
        self,
        detections: Iterable[dict],
        identity_field: str = "label",
    ) -> list[dict]:

        detections = list(detections)
        current_keys = set()
        confirmed = []

        for detection in detections:
            label = str(
                detection.get(identity_field, "unknown")
            )

            track_id = detection.get("track_id")

            key = (
                f"{label}:{track_id}"
                if track_id is not None
                else label
            )

            current_keys.add(key)

            confidence = float(
                detection.get("confidence", 0.0)
            )

            state = self.manager.update(
                key=key,
                detected=True,
                confidence=confidence,
            )

            enriched = dict(detection)
            enriched["confirmed"] = state.confirmed
            enriched["consecutive_hits"] = (
                state.consecutive_hits
            )

            if state.confirmed:
                confirmed.append(enriched)

        for key in list(self.manager.states.keys()):
            if key not in current_keys:
                self.manager.update(
                    key=key,
                    detected=False,
                )

        return confirmed
