from pathlib import Path
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "models" / "hazards" / "boulder.pt"

model = YOLO(str(MODEL_PATH))

print("=" * 70)
print("BOULDER MODEL METADATA")
print("=" * 70)

print("Task:", model.task)
print("Names:", model.names)
print("Model overrides:")

try:
    print(model.overrides)
except Exception as e:
    print("Could not read overrides:", e)

print("\nModel model.yaml:")
try:
    print(model.model.yaml)
except Exception as e:
    print("Could not read yaml:", e)

print("\nModel stride:")
try:
    print(model.model.stride)
except Exception as e:
    print("Could not read stride:", e)