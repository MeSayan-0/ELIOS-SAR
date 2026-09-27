from __future__ import annotations

import time
from typing import Any

from src.core.event_manager import EventManager
from src.core.performance import PerformanceMonitor
from src.core.runtime_state import RuntimeState
from src.core.system_health import SystemHealth
from src.core.serialization import serialize
from src.perception.confirmation import DetectionConfirmation


class HardenedPipeline:
    """
    Safety wrapper around the existing perception pipeline.

    It adds:
    - timing
    - health
    - persistence
    - deduplication
    - structured output
    - exception isolation
    """

    def __init__(
        self,
        base_pipeline,
        person_confirm_hits: int = 3,
        person_clear_misses: int = 5,
        event_cooldown_seconds: float = 3.0,
    ):
        self.base_pipeline = base_pipeline

        self.person_confirmation = DetectionConfirmation(
            confirm_hits=person_confirm_hits,
            clear_misses=person_clear_misses,
        )

        self.events = EventManager(
            cooldown_seconds=event_cooldown_seconds
        )

        self.health = SystemHealth()
        self.performance = PerformanceMonitor()
        self.runtime = RuntimeState()

    def process(self, frame: Any) -> dict:
        self.runtime.frame_id += 1
        self.performance.record_frame()

        start = time.perf_counter()

        try:
            self.health.mark_frame(True)

            raw_result = self.base_pipeline.process(
                frame
            )

            elapsed_ms = (
                time.perf_counter() - start
            ) * 1000.0

            self.performance.record_inference(
                elapsed_ms
            )

            self.health.mark_inference(
                elapsed_ms,
                ok=True,
            )

            result = serialize(raw_result)

            if not isinstance(result, dict):
                result = {
                    "result": result
                }

            persons = result.get(
                "persons",
                result.get("detections", []),
            )

            if not isinstance(persons, list):
                persons = []

            confirmed_persons = (
                self.person_confirmation.process(
                    persons
                )
            )

            result["confirmed_persons"] = (
                confirmed_persons
            )

            result["frame_id"] = (
                self.runtime.frame_id
            )

            result["inference_ms"] = elapsed_ms

            result["performance"] = (
                self.performance.snapshot()
            )

            result["health"] = (
                self.health.snapshot()
            )

            return result

        except Exception as exc:
            self.health.mark_error(exc)

            return {
                "frame_id": self.runtime.frame_id,
                "persons": [],
                "confirmed_persons": [],
                "hazards": [],
                "risk": None,
                "system_status": "pipeline_error",
                "error": str(exc),
                "health": self.health.snapshot(),
            }
