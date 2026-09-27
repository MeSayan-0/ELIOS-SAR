from __future__ import annotations

import time
from collections import deque


class PerformanceMonitor:
    def __init__(self, window_size: int = 30):
        self.window_size = max(5, window_size)
        self.inference_times = deque(
            maxlen=self.window_size
        )
        self.frame_times = deque(
            maxlen=self.window_size
        )
        self.last_frame_time = None

    def record_inference(self, milliseconds: float) -> None:
        self.inference_times.append(
            float(milliseconds)
        )

    def record_frame(self) -> None:
        now = time.perf_counter()

        if self.last_frame_time is not None:
            delta = now - self.last_frame_time

            if delta > 0:
                self.frame_times.append(delta)

        self.last_frame_time = now

    @property
    def average_inference_ms(self) -> float:
        if not self.inference_times:
            return 0.0

        return sum(self.inference_times) / len(
            self.inference_times
        )

    @property
    def fps(self) -> float:
        if not self.frame_times:
            return 0.0

        avg_delta = sum(self.frame_times) / len(
            self.frame_times
        )

        if avg_delta <= 0:
            return 0.0

        return 1.0 / avg_delta

    def snapshot(self) -> dict:
        return {
            "average_inference_ms": round(
                self.average_inference_ms,
                2,
            ),
            "fps": round(self.fps, 2),
            "samples": len(self.inference_times),
        }
