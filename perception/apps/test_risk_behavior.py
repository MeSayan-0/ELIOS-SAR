from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.core.risk_state import PersistentRiskState


risk = PersistentRiskState(
    promote_hits=3,
    demote_hits=5,
)

sequence = [
    ("LOW", 5),
    ("HIGH", 80),
    ("HIGH", 85),
    ("HIGH", 90),
    ("LOW", 5),
    ("LOW", 5),
    ("LOW", 5),
    ("LOW", 5),
    ("LOW", 5),
]

for level, score in sequence:
    state = risk.update(
        level,
        score,
    )

    print(
        f"candidate={level:8} "
        f"score={score:3} "
        f"confirmed={state.level:8} "
        f"smoothed={state.score}"
    )
