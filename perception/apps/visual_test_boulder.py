from pathlib import Path
import cv2
import time
from ultralytics import YOLO


ROOT = Path(__file__).resolve().parents[1]

MODEL_PATH = ROOT / "models" / "hazards" / "boulder.pt"
VIDEO_PATH = ROOT / "testb.mp4"


def main():
    print("=" * 70)
    print("BOULDER MODEL DIAGNOSTIC TEST")
    print("=" * 70)

    print("Model:", MODEL_PATH)
    print("Video:", VIDEO_PATH)

    if not MODEL_PATH.exists():
        print("ERROR: Boulder model not found")
        return

    if not VIDEO_PATH.exists():
        print("ERROR: testb.mp4 not found")
        return

    model = YOLO(str(MODEL_PATH))

    print("Task:", model.task)
    print("Classes:", model.names)

    cap = cv2.VideoCapture(str(VIDEO_PATH))

    if not cap.isOpened():
        print("ERROR: Cannot open video")
        return

    video_fps = cap.get(cv2.CAP_PROP_FPS)
    print("Video FPS:", video_fps)

    paused = False
    frame_number = 0
    last_time = time.time()

    while True:

        if not paused:
            ok, frame = cap.read()

            if not ok:
                print("Video finished")
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

            detection_count = 0

            if result.boxes is not None:
                detection_count = len(result.boxes)

            print(
                f"\rFrame: {frame_number} | "
                f"Detections: {detection_count}",
                end="",
                flush=True,
            )

            # Explicitly request masks, boxes, labels and confidence
            annotated = result.plot(
                boxes=True,
                masks=True,
                labels=True,
                conf=True,
            )

            # Print detection details every 30 frames
            if frame_number % 30 == 0:

                print()

                if detection_count == 0:
                    print("  No rock detected")

                else:
                    for i, box in enumerate(result.boxes):

                        cls_id = int(box.cls[0])
                        confidence = float(box.conf[0])
                        xyxy = box.xyxy[0].tolist()

                        class_name = model.names[cls_id]

                        print(
                            f"  Detection {i + 1}: "
                            f"class={class_name}, "
                            f"confidence={confidence:.3f}, "
                            f"bbox={xyxy}"
                        )

                if result.masks is not None:
                    print(
                        "  Segmentation masks:",
                        len(result.masks)
                    )
                else:
                    print("  Segmentation masks: NONE")

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
                "BOULDER / ROCK SEGMENTATION",
                (12, 29),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.75,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )

            # Status
            cv2.putText(
                annotated,
                f"Detections: {detection_count} | Conf threshold: 0.05",
                (12, 75),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.62,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )

            cv2.imshow(
                "ELIOS-SAR | Boulder Diagnostic",
                annotated,
            )

        key = cv2.waitKey(1 if not paused else 30) & 0xFF

        if key in (ord("q"), ord("Q"), 27):
            break

        if key == 32:
            paused = not paused

    cap.release()
    cv2.destroyAllWindows()

    print("\n")
    print("Boulder diagnostic finished")


if __name__ == "__main__":
    main()