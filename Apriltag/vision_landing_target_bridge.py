import os
import sys
import time
import math
import threading
import cv2
import numpy as np
from pupil_apriltags import Detector
from pymavlink import mavutil

from pose_filter import TargetPoseFilter
from coordinate_transform import CoordinateTransformer

# ==========================================================
# Configuration
# ==========================================================
TAG_FAMILY = "tagStandard41h12"
TARGET_TAG_ID = 0
TAG_SIZE_METERS = 0.20  # Measured physical tag edge width

SERIAL_PORT = "/dev/serial0"
BAUD_RATE = 57600
MAVLINK_TX_RATE_HZ = 15.0  # 15 Hz MAVLink transmission rate

CALIBRATION_FILE = os.path.expanduser("~/Desktop/elios-apriltag/calibration/camera_calibration.npz")

# ==========================================================
# Telemetry Listener Thread (Reads Pixhawk Yaw Heading)
# ==========================================================
class PixhawkTelemetry:
    def __init__(self, connection):
        self.connection = connection
        self.yaw_rad = 0.0
        self.roll_rad = 0.0
        self.pitch_rad = 0.0
        self.connected = False
        self.running = True
        self.lock = threading.Lock()

    def start(self):
        if self.connection is None:
            return
        thread = threading.Thread(target=self._read_loop, daemon=True)
        thread.start()

    def _read_loop(self):
        while self.running:
            try:
                msg = self.connection.recv_match(type="ATTITUDE", blocking=True, timeout=1.0)
                if msg:
                    with self.lock:
                        self.yaw_rad = msg.yaw
                        self.roll_rad = msg.roll
                        self.pitch_rad = msg.pitch
                        self.connected = True
            except Exception:
                time.sleep(0.05)

    def get_attitude(self):
        with self.lock:
            return self.roll_rad, self.pitch_rad, self.yaw_rad, self.connected

    def stop(self):
        self.running = False


def draw_hud_text(img, text, pos, scale=0.6, text_color=(0, 0, 0), outline_color=(255, 255, 255)):
    x, y = pos
    cv2.putText(img, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, scale, outline_color, 4, cv2.LINE_AA)
    cv2.putText(img, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, scale, text_color, 2, cv2.LINE_AA)


def main():
    enable_gui = "--no-gui" not in sys.argv

    print("=" * 70)
    print("ELIOS-SAR Vision to Pixhawk LANDING_TARGET Bridge (Stage 2 + 3)")
    print("=" * 70)
    print("SAFETY GUARD: Passive telemetry only. NO flight controls/ARM sent.")
    print("=" * 70)

    # 1. Load Camera Calibration
    if os.path.exists(CALIBRATION_FILE):
        data = np.load(CALIBRATION_FILE)
        camera_matrix = data["camera_matrix"]
        distortion = data["distortion"]
        is_calibrated = True
        print(f"[Init] Loaded calibration from {CALIBRATION_FILE}")
    else:
        print("[Init WARNING] No camera_calibration.npz found. Using default pinhole model.")
        camera_matrix = np.array([[1000.0, 0.0, 640.0], [0.0, 1000.0, 360.0], [0.0, 0.0, 1.0]], dtype=np.float64)
        distortion = np.zeros((5, 1), dtype=np.float64)
        is_calibrated = False

    camera_params = (
        float(camera_matrix[0, 0]),
        float(camera_matrix[1, 1]),
        float(camera_matrix[0, 2]),
        float(camera_matrix[1, 2])
    )

    # 2. Connect to Pixhawk MAVLink (Optional/Non-blocking)
    mav_conn = None
    telemetry = None
    try:
        print(f"[Init] Attempting connection to Pixhawk on {SERIAL_PORT} @ {BAUD_RATE}...")
        mav_conn = mavutil.mavlink_connection(SERIAL_PORT, baud=BAUD_RATE)
        # Quick non-blocking heartbeat check
        hb = mav_conn.wait_heartbeat(timeout=1.5)
        if hb:
            print(f"[Init] Pixhawk online! System ID: {mav_conn.target_system}")
            telemetry = PixhawkTelemetry(mav_conn)
            telemetry.start()
        else:
            print("[Init NOTICE] No Pixhawk heartbeat detected. Running in VISION-ONLY test mode.")
    except Exception as e:
        print(f"[Init NOTICE] Serial open skipped ({e}). Running in VISION-ONLY test mode.")

    # 3. Setup AprilTag Detector
    detector = Detector(
        families=TAG_FAMILY,
        nthreads=2,
        quad_decimate=2.0,
        quad_sigma=0.0,
        refine_edges=1,
        decode_sharpening=0.25,
        debug=0
    )

    # 4. Filter & Coordinate Transformer
    pose_filter = TargetPoseFilter(alpha=0.30, timeout_sec=0.5)
    transformer = CoordinateTransformer(camera_mount="downward_standard")

    # 5. Open Camera via V4L2
    camera = cv2.VideoCapture(0, cv2.CAP_V4L2)
    if not camera.isOpened():
        print("ERROR: Failed to open camera /dev/video0")
        return

    camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    last_mav_tx = 0.0
    mav_tx_interval = 1.0 / MAVLINK_TX_RATE_HZ
    prev_time = time.time()
    tx_count = 0

    print("\nBridge running. Press 'q' in video window (or Ctrl+C) to quit.\n")

    try:
        while True:
            ret, frame = camera.read()
            if not ret or frame is None:
                break

            if is_calibrated:
                undistorted = cv2.undistort(frame, camera_matrix, distortion)
            else:
                undistorted = frame

            gray = cv2.cvtColor(undistorted, cv2.COLOR_BGR2GRAY)
            detections = detector.detect(
                gray,
                estimate_tag_pose=True,
                camera_params=camera_params,
                tag_size=TAG_SIZE_METERS
            )

            raw_target = None
            for det in detections:
                if det.tag_id == TARGET_TAG_ID:
                    raw_target = det
                    break

            now = time.time()

            if raw_target:
                # Raw camera metric coordinates
                rx = float(raw_target.pose_t[0][0])
                ry = float(raw_target.pose_t[1][0])
                rz = float(raw_target.pose_t[2][0])
                yaw_cam = math.atan2(raw_target.pose_R[1, 0], raw_target.pose_R[0, 0])

                # Smooth with filter
                filtered_pose, is_valid = pose_filter.update(rx, ry, rz, yaw_cam)
                fx, fy, fz, _ = filtered_pose

                # Transform to Drone Body Frame (FRD)
                bx, by, bz = transformer.camera_to_body_frd(fx, fy, fz)

                # Get vehicle yaw from Pixhawk (if connected)
                veh_yaw = 0.0
                pix_connected = False
                if telemetry:
                    _, _, veh_yaw, pix_connected = telemetry.get_attitude()

                # Transform Body FRD to Navigation NED
                nx, ny, nz = transformer.body_frd_to_local_ned(bx, by, bz, veh_yaw)
                angle_x, angle_y, dist = transformer.compute_angles_and_distance(nx, ny, nz)

                # Transmit MAVLink LANDING_TARGET at configured rate
                if mav_conn and (now - last_mav_tx) >= mav_tx_interval:
                    time_usec = int(now * 1_000_000)
                    mav_conn.mav.landing_target_send(
                        time_usec,
                        0,                                   # target_num (0 for primary target)
                        mavutil.mavlink.MAV_FRAME_LOCAL_NED, # coordinate frame
                        angle_x,                             # angle_x (radians)
                        angle_y,                             # angle_y (radians)
                        dist,                                # distance (meters)
                        TAG_SIZE_METERS,                     # size_x (meters)
                        TAG_SIZE_METERS,                     # size_y (meters)
                        nx,                                  # X target position in NED (meters)
                        ny,                                  # Y target position in NED (meters)
                        nz,                                  # Z target position in NED (meters)
                        (1, 0, 0, 0),                        # Quaternion orientation
                        mavutil.mavlink.LANDING_TARGET_TYPE_VISION_FIDUCIAL, # Type 2: Visual fiducial
                        1                                    # position_valid: 1 (required by PX4)
                    )
                    last_mav_tx = now
                    tx_count += 1

                # Visual annotations
                if enable_gui:
                    for i in range(4):
                        p1 = tuple(raw_target.corners[i].astype(int))
                        p2 = tuple(raw_target.corners[(i + 1) % 4].astype(int))
                        cv2.line(undistorted, p1, p2, (0, 255, 0), 2)

                    cx, cy = int(raw_target.center[0]), int(raw_target.center[1])
                    cv2.circle(undistorted, (cx, cy), 6, (0, 0, 255), -1)

                    draw_hud_text(undistorted, f"TARGET LOCKED [ID: {TARGET_TAG_ID}]", (20, 35), 0.75, (0, 150, 0))
                    draw_hud_text(undistorted, f"Camera (X,Y,Z): {fx:+.2f}, {fy:+.2f}, {fz:+.2f} m", (20, 65), 0.65)
                    draw_hud_text(undistorted, f"Body FRD (F,R,D): {bx:+.2f}, {by:+.2f}, {bz:+.2f} m", (20, 95), 0.65)
                    draw_hud_text(undistorted, f"Nav NED (N,E,D):  {nx:+.2f}, {ny:+.2f}, {nz:+.2f} m", (20, 125), 0.65, (0, 0, 180))
                    draw_hud_text(undistorted, f"Distance: {dist:.2f} m | Yaw: {math.degrees(veh_yaw):.1f} deg", (20, 155), 0.65)
            else:
                pose_filter.check_timeout()
                if enable_gui:
                    draw_hud_text(undistorted, f"SEARCHING: AprilTag ID {TARGET_TAG_ID}", (20, 35), 0.75, (0, 0, 180))

            dt = now - prev_time
            fps = 1.0 / dt if dt > 0 else 0.0
            prev_time = now

            if enable_gui:
                status_mav = f"MAVLink TX: {tx_count} pkts" if mav_conn else "MAVLink: Standalone"
                draw_hud_text(undistorted, f"FPS: {fps:.1f} | {status_mav}", (20, 690), 0.6, (50, 50, 50))
                cv2.imshow("ELIOS-SAR Vision Landing Target Bridge", undistorted)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

    except KeyboardInterrupt:
        pass
    finally:
        if telemetry:
            telemetry.stop()
        camera.release()
        cv2.destroyAllWindows()
        print("\nBridge terminated safely.")

if __name__ == "__main__":
    main()
