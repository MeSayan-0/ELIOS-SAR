import os
import time
import math
import cv2
import numpy as np
from pupil_apriltags import Detector

# =========================================
# Configuration
# =========================================
CAMERA_INDEX = 0
TAG_FAMILY = "tagStandard41h12"
TARGET_TAG_ID = 0

# IMPORTANT:
# Actual physical width of the black-to-white square boundary in meters.
# Measure with a ruler and update this value accordingly!
TAG_SIZE = 0.10  # meters (e.g., 0.20 m = 20 cm)

CALIBRATION_FILE = os.path.expanduser("~/Desktop/elios-apriltag/calibration/camera_calibration.npz")

def draw_hud_text(img, text, pos, scale=0.65, text_color=(0, 0, 0), outline_color=(255, 255, 255)):
    x, y = pos
    cv2.putText(img, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, scale, outline_color, 4, cv2.LINE_AA)
    cv2.putText(img, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, scale, text_color, 2, cv2.LINE_AA)

def load_calibration():
    """
    Loads camera matrix and distortion from calibration file.
    Falls back to ideal rectilinear pinhole model if calibration file is missing.
    """
    if os.path.exists(CALIBRATION_FILE):
        data = np.load(CALIBRATION_FILE)
        camera_matrix = data["camera_matrix"]
        distortion = data["distortion"]
        print(f"[Pose] Loaded calibration from {CALIBRATION_FILE}")
        calibrated = True
    else:
        print(f"[Pose WARNING] Calibration file not found at {CALIBRATION_FILE}")
        print("[Pose WARNING] Using standard pinhole estimate (fx=1000, fy=1000, cx=640, cy=360).")
        print("[Pose WARNING] Run calibrate_camera.py for high metric accuracy.")
        camera_matrix = np.array([
            [1000.0, 0.0, 640.0],
            [0.0, 1000.0, 360.0],
            [0.0, 0.0, 1.0]
        ], dtype=np.float64)
        distortion = np.zeros((5, 1), dtype=np.float64)
        calibrated = False

    fx = float(camera_matrix[0, 0])
    fy = float(camera_matrix[1, 1])
    cx = float(camera_matrix[0, 2])
    cy = float(camera_matrix[1, 2])

    camera_params = (fx, fy, cx, cy)
    return camera_matrix, distortion, camera_params, calibrated

def draw_3d_axes(img, camera_matrix, distortion, pose_R, pose_t, axis_length=0.10):
    """
    Projects 3D coordinate axes from the tag center:
    X-axis: Red   (Tag +X)
    Y-axis: Green (Tag +Y)
    Z-axis: Blue  (Tag +Z, pointing outwards toward camera)
    """
    # 3D points in tag coordinate system
    axis_3d = np.float32([
        [0, 0, 0],
        [axis_length, 0, 0],
        [0, axis_length, 0],
        [0, 0, -axis_length]
    ])

    # Convert rotation matrix to rotation vector
    rvec, _ = cv2.Rodrigues(pose_R)
    tvec = pose_t.reshape(3, 1)

    # Project to 2D image plane
    imgpts, _ = cv2.projectPoints(axis_3d, rvec, tvec, camera_matrix, distortion)
    imgpts = imgpts.reshape(-1, 2).astype(int)

    origin = tuple(imgpts[0])
    cv2.line(img, origin, tuple(imgpts[1]), (0, 0, 255), 3)  # X: Red
    cv2.line(img, origin, tuple(imgpts[2]), (0, 255, 0), 3)  # Y: Green
    cv2.line(img, origin, tuple(imgpts[3]), (255, 100, 0), 3) # Z: Blue

def main():
    camera_matrix, distortion, camera_params, is_calibrated = load_calibration()
    fx, fy, cx, cy = camera_params

    print("=" * 60)
    print("ELIOS-SAR 3D AprilTag Pose Estimator (Stage 2)")
    print("=" * 60)
    print(f"Target Family: {TAG_FAMILY} | Target ID: {TARGET_TAG_ID}")
    print(f"Physical Tag Size: {TAG_SIZE * 100:.1f} cm ({TAG_SIZE:.3f} m)")
    print(f"Camera Intrinsics: fx={fx:.1f}, fy={fy:.1f}, cx={cx:.1f}, cy={cy:.1f}")
    print("Press 'q' in video window to exit.")
    print("=" * 60)

    # Detector
    detector = Detector(
        families=TAG_FAMILY,
        nthreads=2,
        quad_decimate=2.0,
        quad_sigma=0.0,
        refine_edges=1,
        decode_sharpening=0.25,
        debug=0
    )

    # Camera with V4L2
    camera = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_V4L2)
    if not camera.isOpened():
        print("ERROR: Failed to open camera via V4L2")
        exit(1)

    camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    prev_time = time.time()

    while True:
        ret, frame = camera.read()
        if not ret or frame is None:
            print("ERROR: Frame read failed.")
            break

        # Undistort if calibration is present
        if is_calibrated:
            undistorted = cv2.undistort(frame, camera_matrix, distortion)
        else:
            undistorted = frame

        gray = cv2.cvtColor(undistorted, cv2.COLOR_BGR2GRAY)

        # Detect and calculate 3D pose
        detections = detector.detect(
            gray,
            estimate_tag_pose=True,
            camera_params=camera_params,
            tag_size=TAG_SIZE
        )

        target_found = False

        for det in detections:
            if det.tag_id != TARGET_TAG_ID:
                continue

            target_found = True
            center = det.center
            corners = det.corners
            pose_t = det.pose_t
            pose_R = det.pose_R

            # Translation vector (Camera optical coordinates: X-right, Y-down, Z-forward)
            x = float(pose_t[0][0])
            y = float(pose_t[1][0])
            z = float(pose_t[2][0])
            distance = math.sqrt(x*x + y*y + z*z)

            # Yaw estimation around camera optical Z axis
            yaw_rad = math.atan2(pose_R[1, 0], pose_R[0, 0])
            yaw_deg = math.degrees(yaw_rad)

            # Draw tag boundary
            for i in range(4):
                p1 = tuple(corners[i].astype(int))
                p2 = tuple(corners[(i + 1) % 4].astype(int))
                cv2.line(undistorted, p1, p2, (0, 255, 0), 2)

            # Tag center
            cx_tag, cy_tag = int(center[0]), int(center[1])
            cv2.circle(undistorted, (cx_tag, cy_tag), 6, (0, 0, 255), -1)

            # Draw 3D coordinate axes
            draw_3d_axes(undistorted, camera_matrix, distortion, pose_R, pose_t)

            # Overlay high-contrast metrics HUD
            draw_hud_text(undistorted, f"Target ID: {det.tag_id}", (20, 40), scale=0.75, text_color=(0, 150, 0))
            draw_hud_text(undistorted, f"X (Lateral):    {x:+.3f} m", (20, 75), scale=0.7, text_color=(0, 0, 0))
            draw_hud_text(undistorted, f"Y (Vertical):   {y:+.3f} m", (20, 105), scale=0.7, text_color=(0, 0, 0))
            draw_hud_text(undistorted, f"Z (Altitude):   {z:+.3f} m", (20, 135), scale=0.7, text_color=(0, 0, 180))
            draw_hud_text(undistorted, f"Distance (3D):  {distance:.3f} m", (20, 165), scale=0.7, text_color=(0, 0, 0))
            draw_hud_text(undistorted, f"Yaw (Optical):  {yaw_deg:+.1f} deg", (20, 195), scale=0.7, text_color=(0, 0, 0))

        if not target_found:
            draw_hud_text(undistorted, f"Searching for AprilTag ID {TARGET_TAG_ID}...", (20, 40), scale=0.75, text_color=(0, 0, 180))

        # Performance overlay
        current_time = time.time()
        fps = 1.0 / (current_time - prev_time) if (current_time - prev_time) > 0 else 0.0
        prev_time = current_time

        status_calib = "Calibrated (NPZ)" if is_calibrated else "Uncalibrated (Pinhole)"
        draw_hud_text(undistorted, f"FPS: {fps:.1f} | {status_calib}", (20, 690), scale=0.6, text_color=(80, 80, 80))

        cv2.imshow("ELIOS-SAR Pose Estimation (Stage 2)", undistorted)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    camera.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
