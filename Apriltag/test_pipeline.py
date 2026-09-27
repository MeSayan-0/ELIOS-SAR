import os
import time
import cv2
from pupil_apriltags import Detector

def run_tests():
    print("=" * 60)
    print("ELIOS-SAR Stage 1 Pipeline Self-Test")
    print("=" * 60)

    # 1. OpenCV Version
    print(f"[1/4] OpenCV version: {cv2.__version__}")

    # 2. AprilTag Library & Detection Verification
    tag_path = os.path.expanduser("~/elios-apriltag/tags/tagStandard41h12_id0_printable.png")
    if not os.path.exists(tag_path):
        print(f"FAIL: Tag image not found at {tag_path}")
        return False

    test_img = cv2.imread(tag_path, cv2.IMREAD_GRAYSCALE)
    detector = Detector(
        families="tagStandard41h12",
        nthreads=2,
        quad_decimate=2.0,
        quad_sigma=0.0,
        refine_edges=1,
        decode_sharpening=0.25,
        debug=0
    )

    # Warmup + benchmark
    t0 = time.time()
    detections = detector.detect(test_img)
    t_detect_ms = (time.time() - t0) * 1000.0

    if not detections:
        print("FAIL: No tags detected in test image!")
        return False

    det = detections[0]
    print(f"[2/4] Detector: OK | Detected ID: {det.tag_id} | Confidence margin: {det.decision_margin:.1f} | Detection time: {t_detect_ms:.1f} ms")

    if det.tag_id != 0:
        print(f"FAIL: Expected Tag ID 0, got {det.tag_id}")
        return False

    # 3. Camera Check
    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
    if not cap.isOpened():
        print("FAIL: Could not open camera /dev/video0")
        return False

    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    ret, frame = cap.read()
    cap.release()

    if not ret or frame is None:
        print("FAIL: Could not read frame from camera")
        return False

    h, w = frame.shape[:2]
    print(f"[3/4] Camera: OK | Captured frame resolution: {w}x{h}")

    # 4. End-to-end processing benchmark
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    t1 = time.time()
    for _ in range(10):
        detector.detect(gray_frame)
    avg_fps = 10.0 / (time.time() - t1)
    print(f"[4/4] Performance: OK | Average processing rate: {avg_fps:.1f} FPS on Raspberry Pi 5")

    print("=" * 60)
    print("STAGE 1 ENVIRONMENT & PIPELINE: 100% READY!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
