from pathlib import Path

from ultralytics import YOLO


MODEL_PATH = "models/thermal/thermal_human.pt"
IMAGE_PATH = "test_images/thermal_test.jpg"

RESULT_DIR = Path("results/thermal")
RESULT_DIR.mkdir(parents=True, exist_ok=True)

print("Loading thermal model...")
model = YOLO(MODEL_PATH)

print("Running thermal human detection...")
results = model.predict(
    source=IMAGE_PATH,
    conf=0.40,
    save=True,
    project=str(RESULT_DIR),
    name="test",
)

print("Thermal detection complete.")

for result in results:
    if result.boxes is None:
        continue

    for box in result.boxes:
        class_id = int(box.cls[0])
        confidence = float(box.conf[0])
        class_name = result.names[class_id]
        print(f"Detected: {class_name} | confidence={confidence:.2f}")
