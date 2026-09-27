from __future__ import annotations

from dataclasses import dataclass, asdict
import time


@dataclass
class HealthState:
    camera_ok: bool = False
    inference_ok: bool = False
    communication_ok: bool = False
    scheduler_ok: bool = True
    last_frame_time: float = 0.0
    last_inference_time: float = 0.0
    last_communication_time: float = 0.0
    inference_ms: float = 0.0
    fps: float = 0.0
    error_count: int = 0
    last_error: str = ""


class SystemHealth:
    def __init__(
        self,
        frame_timeout_seconds: float = 3.0,
        communication_timeout_seconds: float = 5.0,
    ):
        self.state = HealthState()
        self.frame_timeout_seconds = frame_timeout_seconds
        self.communication_timeout_seconds = (
            communication_timeout_seconds
        )

    def mark_frame(self, ok: bool = True) -> None:
        self.state.camera_ok = ok
        self.state.last_frame_time = time.time()

    def mark_inference(
        self,
        inference_ms: float,
        ok: bool = True,
    ) -> None:
        self.state.inference_ok = ok
        self.state.inference_ms = float(inference_ms)
        self.state.last_inference_time = time.time()

    def mark_communication(self, ok: bool = True) -> None:
        self.state.communication_ok = ok
        self.state.last_communication_time = time.time()

    def mark_error(self, error: Exception | str) -> None:
        self.state.error_count += 1
        self.state.last_error = str(error)

    def update_fps(self, fps: float) -> None:
        self.state.fps = float(fps)

    def snapshot(self) -> dict:
        now = time.time()

        camera_recent = (
            now - self.state.last_frame_time
            <= self.frame_timeout_seconds
        )

        communication_recent = (
            self.state.last_communication_time == 0
            or now - self.state.last_communication_time
            <= self.communication_timeout_seconds
        )

        data = asdict(self.state)

        data["camera_recent"] = camera_recent
        data["communication_recent"] = communication_recent
        data["overall_ok"] = (
            camera_recent
            and self.state.inference_ok
            and communication_recent
        )

        return data
