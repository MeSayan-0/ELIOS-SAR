from pathlib import Path
import cv2
import time
import statistics
from ultralytics import YOLO


ROOT = Path(__file__).resolve().parents[1]

MODEL_PATH = ROOT / "models" / "hazards" / "flood.pt"
VIDEO_PATH = ROOT / "testf.mp4"

CONFIDENCE = 0.05
IMGSZ = 640

WARMUP_FRAMES = 5
TEST_FRAMES = 100


def main():
    print("=" * 70)
    print("FLOOD MODEL PERFORMANCE BENCHMARK")
    print("=" * 70)

    model = YOLO(str(MODEL_PATH))
    cap = cv2.VideoCapture(str(VIDEO_PATH))

    if not cap.isOpened():
        print("Could not open video")
        return

    timings = []
    detections = 0
    frames_processed = 0

    print("Warming up model...")

    for _ in range(WARMUP_FRAMES):
        ok, frame = cap.read()
        if not ok:
            break

        model.predict(
            source=frame,
            conf=CONFIDENCE,
            imgsz=IMGSZ,
            device="cpu",
            verbose=False,
        )

    print("Starting benchmark...")

    start_total = time.perf_counter()

    while frames_processed < TEST_FRAMES:
        ok, frame = cap.read()

        if not ok:
            break

        start = time.perf_counter()

        results = model.predict(
            source=frame,
            conf=CONFIDENCE,
            imgsz=IMGSZ,
            device="cpu",
            verbose=False,
        )

        elapsed = time.perf_counter() - start

        timings.append(elapsed)

        result = results[0]

        count = len(result.boxes) if result.boxes is not None else 0

        if count > 0:
            detections += 1

        frames_processed += 1

    total_elapsed = time.perf_counter() - start_total

    if not timings:
        print("No frames processed")
        return

    avg_time = statistics.mean(timings)
    min_time = min(timings)
    max_time = max(timings)
    avg_fps = 1.0 / avg_time
    benchmark_fps = frames_processed / total_elapsed

    print()
    print("=" * 70)
    print("RESULTS")
    print("=" * 70)

    print(f"Frames tested:       {frames_processed}")
    print(f"Average inference:   {avg_time * 1000:.2f} ms")
    print(f"Minimum inference:   {min_time * 1000:.2f} ms")
    print(f"Maximum inference:   {max_time * 1000:.2f} ms")
    print(f"Average AI FPS:      {avg_fps:.2f}")
    print(f"Benchmark FPS:       {benchmark_fps:.2f}")
    print(f"Frames with water:   {detections}/{frames_processed}")
    print(f"Detection percentage:{(detections / frames_processed) * 100:.1f}%")

    print()
    print("Interpretation:")

    if avg_fps >= 15:
        print("Fast enough for frequent near-real-time inference")

    elif avg_fps >= 5:
        print("Moderate speed; frame skipping recommended")

    else:
        print("Slow on CPU; scheduler/frame skipping required")


if __name__ == "__main__":
    main()