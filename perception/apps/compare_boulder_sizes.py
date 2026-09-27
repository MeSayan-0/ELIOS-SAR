from pathlib import Path
import cv2
import time
from ultralytics import YOLO


ROOT = Path(__file__).resolve().parents[1]

MODEL_PATH = ROOT / "models" / "hazards" / "boulder.pt"
VIDEO_PATH = ROOT / "testb.mp4"

CONFIDENCE = 0.05
TEST_SIZES = [320, 640, 1280]


def main():
    model = YOLO(str(MODEL_PATH))

    cap = cv2.VideoCapture(str(VIDEO_PATH))

    if not cap.isOpened():
        print("Could not open video")
        return

    print("Testing one frame at different inference sizes...")
    print()

    # Read a frame containing visible rocks
    target_frame = None

    while True:
        ok, frame = cap.read()

        if not ok:
            break

        target_frame = frame

        # Use approximately frame 30
        if int(cap.get(cv2.CAP_PROP_POS_FRAMES)) >= 30:
            break

    cap.release()

    if target_frame is None:
        print("No frame found")
        return

    print("Original frame shape:", target_frame.shape)

    for size in TEST_SIZES:
        print("\n" + "=" * 60)
        print("INFERENCE SIZE:", size)
        print("=" * 60)

        start = time.time()

        results = model.predict(
            source=target_frame,
            conf=CONFIDENCE,
            imgsz=size,
            device="cpu",
            verbose=False,
        )

        elapsed = time.time() - start
        result = results[0]

        boxes = result.boxes
        masks = result.masks

        box_count = len(boxes) if boxes is not None else 0
        mask_count = len(masks) if masks is not None else 0

        print("Inference time:", round(elapsed, 3), "seconds")
        print("Boxes:", box_count)
        print("Masks:", mask_count)

        if boxes is not None:
            for i, box in enumerate(boxes):
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                bbox = box.xyxy[0].tolist()

                print(
                    f"Detection {i + 1}: "
                    f"class={model.names[cls_id]}, "
                    f"confidence={conf:.4f}, "
                    f"bbox={bbox}"
                )

        annotated = result.plot(
            boxes=True,
            masks=True,
            labels=True,
            conf=True,
        )

        cv2.imshow(
            f"Boulder Test - imgsz {size}",
            annotated,
        )

        print("Press any key in image window to continue...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()