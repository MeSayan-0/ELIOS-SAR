from pathlib import Path

from ultralytics import YOLO


MODEL_PATH = "models/rgb/rgb_disaster.pt"
IMAGE_PATH = "test_images/rgb_test.jpg"

RESULT_DIR = Path("results/rgb")
RESULT_DIR.mkdir(parents=True, exist_ok=True)

print("Loading RGB model...")
model = YOLO(MODEL_PATH)

print("Running RGB detection...")
results = model.predict(
    source=IMAGE_PATH,
    conf=0.40,
    save=True,
    project=str(RESULT_DIR),
    name="test",
)

print("RGB detection complete.")

for result in results:
    if result.boxes is None:
        continue

    for box in result.boxes:
        class_id = int(box.cls[0])
        confidence = float(box.conf[0])
        class_name = result.names[class_id]
        print(f"Detected: {class_name} | confidence={confidence:.2f}")
