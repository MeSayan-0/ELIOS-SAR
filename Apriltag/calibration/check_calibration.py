import os
import cv2
import numpy as np

CALIBRATION_FILE = os.path.expanduser("~/Desktop/elios-apriltag/calibration/camera_calibration.npz")

def main():
    if not os.path.exists(CALIBRATION_FILE):
        print(f"ERROR: Calibration file not found at {CALIBRATION_FILE}")
        print("Please run 'python calibrate_camera.py' first.")
        exit(1)

    data = np.load(CALIBRATION_FILE)
    camera_matrix = data["camera_matrix"]
    distortion = data["distortion"]

    print("Loaded calibration:")
    print("Camera Matrix:\n", camera_matrix)
    print("Distortion:\n", distortion)

    camera = cv2.VideoCapture(0, cv2.CAP_V4L2)
    if not camera.isOpened():
        print("ERROR: Camera failed to open with V4L2")
        exit(1)

    camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    print("\nDisplaying Original vs Undistorted feed. Press 'q' to quit.")

    while True:
        ret, frame = camera.read()
        if not ret or frame is None:
            break

        undistorted = cv2.undistort(frame, camera_matrix, distortion)

        # Draw labels
        cv2.putText(frame, "Original (Raw Lens Distortion)", (30, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 4, cv2.LINE_AA)
        cv2.putText(frame, "Original (Raw Lens Distortion)", (30, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 2, cv2.LINE_AA)

        cv2.putText(undistorted, "Undistorted (Calibrated Rectilinear)", (30, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 4, cv2.LINE_AA)
        cv2.putText(undistorted, "Undistorted (Calibrated Rectilinear)", (30, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 150, 0), 2, cv2.LINE_AA)

        # Show side-by-side or scaled
        h, w = frame.shape[:2]
        combined = np.hstack([cv2.resize(frame, (w // 2, h // 2)),
                              cv2.resize(undistorted, (w // 2, h // 2))])

        cv2.imshow("ELIOS-SAR Calibration Verification (Left: Raw | Right: Undistorted)", combined)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    camera.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
