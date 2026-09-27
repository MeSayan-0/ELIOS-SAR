import os
import sys
import cv2
import time
from ultralytics import YOLO

VIDEO_PATH = "recordings/test_input.mp4"
if not os.path.exists(VIDEO_PATH):
    if os.path.exists("test.mp4"):
        VIDEO_PATH = "test.mp4"
    elif os.path.exists("recordings/test_output.mp4"):
        VIDEO_PATH = "recordings/test_output.mp4"

if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
    VIDEO_PATH = sys.argv[1]

MODELS = {
    "ROCK": "models/hazards/boulder.pt",
    "FLOOD": "models/hazards/flood.pt",
}


def run_test(name, model_path):
    print(f"\n===== TESTING {name} =====")
    print(f"Video: {VIDEO_PATH}")

    model = YOLO(model_path)

    cap = cv2.VideoCapture(VIDEO_PATH)

    if not cap.isOpened():
        print(f"Could not open video: {VIDEO_PATH}")
        return

    frame_count = 0
    detection_count = 0
    start = time.perf_counter()

    while True:
        ok, frame = cap.read()

        if not ok:
            break

        results = model.predict(
            source=frame,
            conf=0.25,
            imgsz=320,
            device="cpu",
            verbose=False
        )

        result = results[0]

        if result.boxes is not None:
            count = len(result.boxes)

            if count > 0:
                detection_count += count

                print(
                    f"[{name}] frame={frame_count} "
                    f"detections={count}"
                )

        annotated = result.plot()

        try:
            cv2.imshow(name, annotated)
            if cv2.waitKey(1) & 0xFF == 27:
                break
        except Exception:
            pass

        frame_count += 1

        # Diagnostic stop: let's test initial batch of frames if long video
        # (user requested short test: 300 frames)
        if frame_count >= 300:
            print(f"[{name}] Reached 300 diagnostic test frames.")
            break

    elapsed = time.perf_counter() - start

    print(f"\n{name} RESULTS")
    print(f"Frames: {frame_count}")
    print(f"Detections: {detection_count}")
    print(f"Time: {elapsed:.2f}s")
    print(f"FPS: {frame_count / elapsed:.2f}" if elapsed > 0 else "FPS: N/A")

    cap.release()
    try:
        cv2.destroyAllWindows()
    except Exception:
        pass


for name, model_path in MODELS.items():
    run_test(name, model_path)
