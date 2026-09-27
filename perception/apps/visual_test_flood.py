from pathlib import Path
import cv2
import time
from ultralytics import YOLO


ROOT = Path(__file__).resolve().parents[1]

MODEL_PATH = ROOT / "models" / "hazards" / "flood.pt"
VIDEO_PATH = ROOT / "testf.mp4"


def main():
    print("=" * 70)
    print("FLOOD / WATER SEGMENTATION DIAGNOSTIC TEST")
    print("=" * 70)

    print("Model:", MODEL_PATH)
    print("Video:", VIDEO_PATH)

    if not MODEL_PATH.exists():
        print("ERROR: Flood model not found")
        return

    if not VIDEO_PATH.exists():
        print("ERROR: testf.mp4 not found")
        return

    print("Loading model...")
    model = YOLO(str(MODEL_PATH))

    print("Task:", model.task)
    print("Classes:", model.names)

    cap = cv2.VideoCapture(str(VIDEO_PATH))

    if not cap.isOpened():
        print("ERROR: Cannot open flood video")
        return

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    print(f"Video: {width}x{height}")
    print(f"FPS: {fps}")
    print(f"Frames: {total_frames}")
    print("Press Q or ESC to exit")
    print("Press SPACE to pause/resume")

    paused = False
    frame_number = 0
    last_report = time.time()

    while True:

        if not paused:
            ok, frame = cap.read()

            if not ok:
                print("\nVideo finished")
                break

            frame_number += 1

            results = model.predict(
                source=frame,
                conf=0.05,
                imgsz=640,
                device="cpu",
                verbose=False,
            )

            result = results[0]

            detection_count = (
                len(result.boxes)
                if result.boxes is not None
                else 0
            )

            mask_count = (
                len(result.masks)
                if result.masks is not None
                else 0
            )

            # Print every 30 frames
            if frame_number % 30 == 0:
                print(
                    f"Frame {frame_number}/{total_frames} | "
                    f"Water regions: {detection_count} | "
                    f"Masks: {mask_count}"
                )

                if result.boxes is not None:
                    for i, box in enumerate(result.boxes):
                        cls_id = int(box.cls[0])
                        confidence = float(box.conf[0])
                        bbox = box.xyxy[0].tolist()

                        print(
                            f"  Detection {i + 1}: "
                            f"class={model.names[cls_id]}, "
                            f"confidence={confidence:.3f}, "
                            f"bbox={bbox}"
                        )

            annotated = result.plot(
                boxes=True,
                masks=True,
                labels=True,
                conf=True,
            )

            # Header
            cv2.rectangle(
                annotated,
                (0, 0),
                (annotated.shape[1], 42),
                (0, 0, 0),
                -1,
            )

            cv2.putText(
                annotated,
                "FLOOD / WATER SEGMENTATION",
                (12, 29),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.75,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )

            cv2.putText(
                annotated,
                (
                    f"Water regions: {detection_count} | "
                    f"Masks: {mask_count} | "
                    f"Frame: {frame_number}"
                ),
                (12, 75),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.60,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )

            cv2.imshow(
                "ELIOS-SAR | Flood Diagnostic",
                annotated,
            )

        key = cv2.waitKey(1 if not paused else 30) & 0xFF

        if key in (ord("q"), ord("Q"), 27):
            break

        if key == 32:
            paused = not paused

    cap.release()
    cv2.destroyAllWindows()

    print("\nFlood diagnostic finished")


if __name__ == "__main__":
    main()