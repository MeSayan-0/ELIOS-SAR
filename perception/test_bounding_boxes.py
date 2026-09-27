import argparse
from pathlib import Path
import sys
import time
import cv2
from ultralytics import YOLO

DETECTOR_CONFIG = {
    "person": {
        "model": "models/rgb/rgb_disaster.pt",
        "conf": 0.35,
        "imgsz": 640,
        "color": (0, 255, 0),
        "desc": "Person / Disaster RGB Detector",
    },
    "boulder": {
        "model": "models/hazards/boulder.pt",
        "conf": 0.25,
        "imgsz": 320,
        "color": (42, 42, 165),
        "desc": "Boulder / Rockfall Detector",
    },
    "fire": {
        "model": "models/hazards/fire.pt",
        "conf": 0.30,
        "imgsz": 320,
        "color": (0, 0, 255),
        "desc": "Fire & Smoke Detector",
    },
    "flood": {
        "model": "models/hazards/flood.pt",
        "conf": 0.25,
        "imgsz": 320,
        "color": (255, 0, 0),
        "desc": "Flood / Water Detector",
    },
}

parser = argparse.ArgumentParser(
    description="ELIOS-SAR Single Detector Real-Time Bounding Box Test (Every Frame)"
)
parser.add_argument(
    "--detector",
    choices=list(DETECTOR_CONFIG.keys()),
    default="person",
    help="Select which AI detector to run exclusively on every frame (default: person)",
)
parser.add_argument(
    "--camera-id",
    type=int,
    default=0,
    help="Webcam device index (default: 0)",
)
parser.add_argument(
    "--conf",
    type=float,
    default=None,
    help="Override default confidence threshold",
)
import queue
import threading

parser.add_argument(
    "--model",
    type=str,
    default=None,
    help="Override default model weights path",
)
parser.add_argument(
    "--width",
    type=int,
    default=640,
    help="Camera width (default: 640)",
)
parser.add_argument(
    "--height",
    type=int,
    default=480,
    help="Camera height (default: 480)",
)

args = parser.parse_args()

cfg = DETECTOR_CONFIG[args.detector]
model_path = args.model if args.model else cfg["model"]
confidence = args.conf if args.conf is not None else cfg["conf"]
imgsz = cfg["imgsz"]
box_color = cfg["color"]
camera_id = args.camera_id

print("=" * 60)
print(f"ELIOS-SAR SINGLE DETECTOR TEST: {args.detector.upper()}")
print("=" * 60)
print(f"Description : {cfg['desc']}")
print(f"Model       : {model_path}")
print(f"Camera      : {camera_id} ({args.width}x{args.height} MJPG)")
print(f"Confidence  : {confidence}")
print(f"Inference   : DECOUPLED BACKGROUND WORKER (imgsz={imgsz})")
print("Mode        : 30 FPS BUTTER-SMOOTH DISPLAY")
print("NO GCS / NO TCP / NO ROS (Standalone Window)")
print("=" * 60)

# Load YOLO model
print("\nLoading model...")
model = YOLO(model_path)
print(f"Model loaded. Available classes: {model.names}")

# Open webcam
print("\nOpening webcam...")
cap = cv2.VideoCapture(camera_id)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)

if not cap.isOpened():
    raise RuntimeError(f"Could not open webcam device {camera_id}")

print("Webcam opened.")


class CachedDetectionState:
    """Thread-safe cache holding latest AI detections with freshness timeout."""

    def __init__(self, freshness_timeout: float = 1.5):
        self.freshness_timeout = float(freshness_timeout)
        self.lock = threading.Lock()
        self.detections = []
        self.last_updated = 0.0

    def update(self, detections):
        with self.lock:
            self.detections = list(detections)
            self.last_updated = time.time()

    def get_fresh_detections(self):
        with self.lock:
            if not self.detections:
                return []
            if time.time() - self.last_updated > self.freshness_timeout:
                return []
            return list(self.detections)


cached_state = CachedDetectionState(freshness_timeout=1.5)
ai_input_queue: queue.Queue = queue.Queue(maxsize=1)
running = True


def ai_worker_loop():
    """Background AI inference loop decoupled from camera display rate (like apps/elios_sar.py)."""
    while running:
        try:
            item = ai_input_queue.get(timeout=0.2)
        except queue.Empty:
            continue

        if item is None:
            break

        img_for_ai = item

        try:
            results = model.predict(
                source=img_for_ai,
                conf=confidence,
                verbose=False,
                imgsz=imgsz,
            )
            result = results[0]

            detections = []
            if result.boxes is not None:
                for box in result.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    conf_val = float(box.conf[0])
                    class_id = int(box.cls[0])
                    class_name = result.names[class_id]
                    detections.append(
                        (int(x1), int(y1), int(x2), int(y2), class_name, conf_val)
                    )

            cached_state.update(detections)

        except Exception as exc:
            pass


ai_thread = threading.Thread(
    target=ai_worker_loop,
    name="AI-Worker",
    daemon=True,
)
ai_thread.start()

print("\nStarting detection...")
print("Press Q to quit.\n")

frame_count = 0
last_time = time.time()
retry_count = 0

try:
    while True:
        ret, frame = cap.read()

        if not ret or frame is None:
            retry_count += 1
            if retry_count > 10:
                print("Failed to read frame after 10 attempts")
                break
            time.sleep(0.05)
            continue
        retry_count = 0

        frame_count += 1

        # Submit frame copy to background AI worker if ready (drop if busy -> zero lag!)
        try:
            ai_input_queue.put_nowait(frame.copy())
        except queue.Full:
            pass

        # Draw latest fresh detections from cache
        active_detections = cached_state.get_fresh_detections()

        for (x1, y1, x2, y2, class_name, conf_val) in active_detections:
            # Draw bounding box
            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                box_color,
                2,
            )

            # Label
            label = f"{class_name.upper()} {conf_val:.2f}"

            # Label background badge
            (tw, th), _ = cv2.getTextSize(
                label,
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                2,
            )

            cv2.rectangle(
                frame,
                (x1, y1 - th - 10),
                (x1 + tw + 5, y1),
                box_color,
                -1,
            )

            # Contrast text: dark on bright colors, white on dark
            text_color = (
                (0, 0, 0)
                if (box_color[0] + box_color[1] + box_color[2]) > 350
                else (255, 255, 255)
            )
            cv2.putText(
                frame,
                label,
                (x1 + 2, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                text_color,
                2,
            )

        # FPS calculation
        now = time.time()
        fps = 1.0 / max(now - last_time, 0.001)
        last_time = now

        # Information banner on image
        info = f"FPS: {fps:.1f} (SMOOTH) | [{args.detector.upper()}] Detections: {len(active_detections)}"

        cv2.putText(
            frame,
            info,
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            (0, 255, 255),
            2,
        )

        # Show image locally
        window_title = f"ELIOS-SAR | {args.detector.upper()} Detector (Smooth Decoupled)"
        cv2.imshow(window_title, frame)

        key = cv2.waitKey(1) & 0xFF
        if key in (ord("q"), 27):
            break

finally:
    running = False
    try:
        ai_input_queue.put_nowait(None)
    except Exception:
        pass
    ai_thread.join(timeout=1.0)
    cap.release()
    cv2.destroyAllWindows()

print("\nTest stopped.")
print(f"Frames processed: {frame_count}")
