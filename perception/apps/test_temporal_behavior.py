from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.core.temporal_state import TemporalStateManager


manager = TemporalStateManager(
    confirm_hits=3,
    clear_misses=5,
)

print("Frame 1:", manager.update(
    "person_1",
    True,
    0.60,
))

print("Frame 2:", manager.update(
    "person_1",
    True,
    0.70,
))

print("Frame 3:", manager.update(
    "person_1",
    True,
    0.80,
))

print("Confirmed:", manager.is_confirmed("person_1"))

for index in range(5):
    state = manager.update(
        "person_1",
        False,
    )

    print(
        f"Miss {index + 1}:",
        state.confirmed,
    )
