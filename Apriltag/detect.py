import time
import cv2
from pupil_apriltags import Detector

def draw_text(img, text, pos, scale=0.7, text_color=(0, 0, 0), outline_color=(255, 255, 255)):
    """
    Renders bold dark text with a crisp light outline so it stands out sharply
    against white tag surfaces as well as dark floors.
    """
    x, y = pos
    # Light outline (thickness=4)
    cv2.putText(img, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, scale, outline_color, 4, cv2.LINE_AA)
    # Dark font (thickness=2)
    cv2.putText(img, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, scale, text_color, 2, cv2.LINE_AA)

def main():
    # -----------------------------
    # Camera Initialization
    # -----------------------------
    # Use cv2.CAP_V4L2 explicitly to avoid GStreamer stalling on Linux/Raspberry Pi
    camera = cv2.VideoCapture(0, cv2.CAP_V4L2)

    if not camera.isOpened():
        print("ERROR: Could not open camera with V4L2 backend")
        exit(1)

    # Configure MJPG compression, resolution, and zero-latency single-frame buffer
    camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    actual_width = int(camera.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_height = int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"Camera opened successfully: {actual_width}x{actual_height} (V4L2 backend)")

    # -----------------------------
    # AprilTag Detector Configuration
    # -----------------------------
    detector = Detector(
        families="tagStandard41h12",
        nthreads=2,
        quad_decimate=2.0,
        quad_sigma=0.0,
        refine_edges=1,
        decode_sharpening=0.25,
        debug=0
    )

    print("ELIOS-SAR AprilTag detector started.")
    print("Target Family: tagStandard41h12")
    print("Press 'q' in the video window to quit.")

    prev_time = time.time()

    while True:
        ret, frame = camera.read()

        if not ret or frame is None:
            print("ERROR: Could not read camera frame")
            break

        # Convert to grayscale for detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect AprilTags
        detections = detector.detect(gray)

        # Draw every detection
        for detection in detections:
            tag_id = detection.tag_id
            center = detection.center
            corners = detection.corners

            # -----------------------------
            # Draw corners (Green quadrilateral)
            # -----------------------------
            for i in range(4):
                p1 = tuple(corners[i].astype(int))
                p2 = tuple(corners[(i + 1) % 4].astype(int))
                cv2.line(frame, p1, p2, (0, 255, 0), 2)

            # -----------------------------
            # Draw center (Red point)
            # -----------------------------
            cx = int(center[0])
            cy = int(center[1])
            cv2.circle(frame, (cx, cy), 6, (0, 0, 255), -1)

            # -----------------------------
            # Display ID (Bold dark font on white outline)
            # -----------------------------
            text = f"AprilTag ID: {tag_id}"
            draw_text(frame, text, (cx + 10, cy), scale=0.7, text_color=(0, 0, 0), outline_color=(255, 255, 255))

            # -----------------------------
            # Display center coordinates (Bold dark font on white outline)
            # -----------------------------
            position_text = f"Center: ({cx}, {cy})"
            draw_text(frame, position_text, (cx + 10, cy + 28), scale=0.6, text_color=(0, 0, 0), outline_color=(255, 255, 255))

        # -----------------------------
        # FPS Measurement & Display
        # -----------------------------
        current_time = time.time()
        dt = current_time - prev_time
        fps = (1.0 / dt) if dt > 0 else 0.0
        prev_time = current_time

        # Top-left HUD with dark font and white outline for clean readability
        draw_text(frame, f"Detections: {len(detections)}", (20, 40), scale=0.8, text_color=(0, 0, 0), outline_color=(255, 255, 255))
        draw_text(frame, f"FPS: {fps:.1f}", (20, 75), scale=0.8, text_color=(0, 0, 180), outline_color=(255, 255, 255))

        cv2.imshow("ELIOS-SAR AprilTag Detection", frame)

        # Quit with Q
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    camera.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
