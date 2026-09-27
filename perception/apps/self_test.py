from __future__ import annotations

from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.core.temporal_state import TemporalStateManager
from src.core.event_manager import EventManager
from src.core.risk_state import PersistentRiskState
from src.core.system_health import SystemHealth
from src.core.performance import PerformanceMonitor
from src.core.serialization import serialize
from src.core.contracts import RiskResult


def check(name, callback):
    try:
        callback()
        print(f"[PASS] {name}")
        return True
    except Exception as exc:
        print(f"[FAIL] {name}: {exc}")
        return False


def main():
    checks = []

    checks.append(
        check(
            "Temporal state",
            lambda: (
                TemporalStateManager()
                .update("person", True)
            ),
        )
    )

    checks.append(
        check(
            "Event manager",
            lambda: EventManager().should_emit(
                "test",
                "identity",
            ),
        )
    )

    checks.append(
        check(
            "Risk state",
            lambda: PersistentRiskState().update(
                "LOW",
                0,
            ),
        )
    )

    checks.append(
        check(
            "Serialization",
            lambda: serialize(
                RiskResult(
                    level="LOW",
                    score=0,
                )
            ),
        )
    )

    checks.append(
        check(
            "Health",
            lambda: SystemHealth().snapshot(),
        )
    )

    checks.append(
        check(
            "Performance",
            lambda: PerformanceMonitor().snapshot(),
        )
    )

    passed = sum(checks)
    total = len(checks)

    print()
    print(f"Self-test result: {passed}/{total}")

    if passed != total:
        sys.exit(1)


if __name__ == "__main__":
    main()
