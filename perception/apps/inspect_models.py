from pathlib import Path
from ultralytics import YOLO

MODELS = [
    ("RGB MODEL", "models/rgb/rgb_disaster.pt"),
    ("FIRE MODEL", "models/hazards/fire.pt"),
    ("FLOOD MODEL", "models/hazards/flood.pt"),
    ("BOULDER MODEL", "models/hazards/boulder.pt"),
    ("POSE MODEL", "models/pose/yolo11n-pose.pt"),
]

ROOT = Path(__file__).resolve().parents[1]

for name, relative_path in MODELS:
    print("\n" + "=" * 70)
    print(name)
    print("=" * 70)

    path = ROOT / relative_path

    print("Path:", path)
    print("Exists:", path.exists())

    if not path.exists():
        print("SKIPPED - FILE NOT FOUND")
        continue

    try:
        model = YOLO(str(path))

        print("Task:", model.task)
        print("Names:", model.names)

        if hasattr(model, "ckpt") and model.ckpt:
            print("Checkpoint loaded successfully")

    except Exception as error:
        print("ERROR:", repr(error))
