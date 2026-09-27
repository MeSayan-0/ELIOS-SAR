from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.perception.ai_scheduler import AIScheduler


class FakeDetector:
    def __init__(self, name):
        self.name = name

    def detect(self, frame):
        print(f"Running: {self.name}")
        return [{"source": self.name}]


scheduler = AIScheduler(
    fire_detector=FakeDetector("fire"),
    flood_detector=FakeDetector("flood"),
    boulder_detector=FakeDetector("boulder"),
    fire_interval=4,
    flood_interval=8,
    boulder_interval=2
)

frame = np.zeros((480, 640, 3), dtype=np.uint8)

for index in range(16):
    print(f"\nFrame {index}")
    result = scheduler.run(frame)
    print(result)
