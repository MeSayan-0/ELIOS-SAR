from __future__ import annotations

import importlib
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

MODULES = [
    "src.core.contracts",
    "src.core.serialization",
    "src.core.temporal_state",
    "src.core.event_manager",
    "src.core.system_health",
    "src.core.risk_state",
    "src.core.performance",
    "src.core.runtime_state",
    "src.core.event_builder",
    "src.core.safe_emitter",
    "src.perception.confirmation",
    "src.communication.telemetry_queue",
]


def main():
    failures = []

    for module_name in MODULES:
        try:
            importlib.import_module(module_name)
            print(f"[PASS] {module_name}")
        except Exception as exc:
            print(
                f"[FAIL] {module_name}: {exc}"
            )
            failures.append(module_name)

    print()

    if failures:
        print("Failed modules:")
        for module in failures:
            print(f" - {module}")

        sys.exit(1)

    print("All modules imported successfully.")


if __name__ == "__main__":
    main()
