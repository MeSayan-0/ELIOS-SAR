from pathlib import Path
import sys
import cv2

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from drone.config import BOULDER_MODEL_PATH, BOULDER_CONFIDENCE, BOULDER_IMAGE_SIZE
from src.perception.boulder_detector import BoulderDetector


IMAGE_PATH = ROOT / "test_boulder.jpg"

if not IMAGE_PATH.exists():
    raise FileNotFoundError(
        f"Put a test image at: {IMAGE_PATH}"
    )

frame = cv2.imread(str(IMAGE_PATH))

if frame is None:
    raise RuntimeError("Could not read test image")

detector = BoulderDetector(
    model_path=BOULDER_MODEL_PATH,
    confidence=BOULDER_CONFIDENCE,
    image_size=BOULDER_IMAGE_SIZE
)

detections = detector.detect(frame)

print("\nBOULDER DETECTIONS")
print("=================")

for detection in detections:
    print(detection)

for detection in detections:
    x1, y1, x2, y2 = map(int, detection.bbox)

    cv2.rectangle(
        frame,
        (x1, y1),
        (x2, y2),
        (0, 0, 255),
        2
    )

    text = (
        f"{detection.class_name} "
        f"{detection.confidence:.2f} "
        f"{detection.obstruction_level}"
    )

    cv2.putText(
        frame,
        text,
        (x1, max(20, y1 - 10)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (0, 0, 255),
        2
    )

cv2.imshow("Boulder Test", frame)
cv2.waitKey(0)
cv2.destroyAllWindows()
