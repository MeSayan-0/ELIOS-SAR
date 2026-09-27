from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from drone.config import (
    MODEL_PATH,
    POSE_MODEL_PATH,
    FIRE_MODEL_PATH,
    FLOOD_MODEL_PATH,
    BOULDER_MODEL_PATH,
    ENABLE_FIRE,
    ENABLE_FLOOD,
    ENABLE_BOULDER,
    ENABLE_POSE
)

from ultralytics import YOLO


def resolve(path):
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    return p


models = [
    ("PERSON", MODEL_PATH, True),
    ("POSE", POSE_MODEL_PATH, ENABLE_POSE),
    ("FIRE", FIRE_MODEL_PATH, ENABLE_FIRE),
    ("FLOOD", FLOOD_MODEL_PATH, ENABLE_FLOOD),
    ("BOULDER", BOULDER_MODEL_PATH, ENABLE_BOULDER),
]

for name, path, enabled in models:
    resolved = resolve(path)

    if not enabled:
        print(f"[DISABLED] {name}")
        continue

    print(f"\nLoading {name}")
    print(f"Path: {resolved}")

    if not resolved.exists():
        print(f"[FAIL] Missing file: {resolved}")
        continue

    try:
        model = YOLO(str(resolved))
        print(f"[OK] {name}")
        print(f"Classes: {model.names}")
    except Exception as exc:
        print(f"[FAIL] {name}: {exc}")

print("\nModel loading test complete.")
