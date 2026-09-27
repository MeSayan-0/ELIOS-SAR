import math

try:
    from drone.config import FIRE_RATE, FLOOD_RATE, BOULDER_RATE
except ImportError:
    FIRE_RATE = 0.75
    FLOOD_RATE = 0.0
    BOULDER_RATE = 0.50


class AIScheduler:
    def __init__(
        self,
        fire_detector=None,
        flood_detector=None,
        boulder_detector=None,
        fire_interval=None,
        flood_interval=None,
        boulder_interval=None,
        fire_rate: float | None = None,
        flood_rate: float | None = None,
        boulder_rate: float | None = None,
    ):
        self.fire_detector = fire_detector
        self.flood_detector = flood_detector
        self.boulder_detector = boulder_detector

        # Resolve rates: explicit rate > explicit interval > env config
        self.fire_rate = self._resolve_rate(fire_rate, fire_interval, default_rate=FIRE_RATE)
        self.flood_rate = self._resolve_rate(flood_rate, flood_interval, default_rate=FLOOD_RATE)
        self.boulder_rate = self._resolve_rate(boulder_rate, boulder_interval, default_rate=BOULDER_RATE)

        # Track effective intervals for legacy inspection
        self.fire_interval = int(round(1.0 / self.fire_rate)) if self.fire_rate > 0 else 0
        self.flood_interval = int(round(1.0 / self.flood_rate)) if self.flood_rate > 0 else 0
        self.boulder_interval = int(round(1.0 / self.boulder_rate)) if self.boulder_rate > 0 else 0

        self.frame_counter = 0

    @staticmethod
    def _resolve_rate(rate, interval, default_rate: float) -> float:
        if rate is not None:
            return max(0.0, min(1.0, float(rate)))
        if interval is not None:
            if interval <= 0:
                return 0.0
            return max(0.0, min(1.0, 1.0 / float(interval)))
        return default_rate

    @staticmethod
    def _should_run(rate: float, frame: int) -> bool:
        if rate <= 0.0:
            return False
        if rate >= 1.0:
            return True
        return math.floor(frame * rate) != math.floor((frame - 1) * rate)

    def run(self, frame):
        current_frame = self.frame_counter
        self.frame_counter += 1

        results = {
            "fire": [],
            "flood": [],
            "boulder": []
        }

        if (
            self.fire_detector is not None and
            self._should_run(self.fire_rate, current_frame)
        ):
            results["fire"] = self.fire_detector.detect(frame)

        if (
            self.flood_detector is not None and
            self._should_run(self.flood_rate, current_frame)
        ):
            results["flood"] = self.flood_detector.detect(frame)

        if (
            self.boulder_detector is not None and
            self._should_run(self.boulder_rate, current_frame)
        ):
            results["boulder"] = self.boulder_detector.detect(frame)

        return results
