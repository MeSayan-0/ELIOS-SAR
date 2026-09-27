import sys
import glob
import time
import math
from pymavlink import mavutil

DEFAULT_PORTS = ["/dev/serial0", "/dev/ttyAMA0", "/dev/ttyUSB0", "/dev/ttyACM0"]
BAUD_RATE = 57600
RATE_HZ = 10.0  # 10 Hz transmission rate

def find_serial_port():
    if len(sys.argv) > 1:
        return sys.argv[1]
    for p in DEFAULT_PORTS:
        if glob.glob(p):
            return p
    return "/dev/serial0"

def main():
    serial_port = find_serial_port()
    print("=" * 65)
    print("ELIOS-SAR Synthetic LANDING_TARGET Sender (Stage 3 Verification)")
    print("=" * 65)
    print("SAFETY NOTICE:")
    print("- This script ONLY transmits passive target coordinate telemetry.")
    print("- NO ARM, TAKEOFF, LAND, or motor controls are executed.")
    print(f"- Target rate: {RATE_HZ} Hz on {serial_port} @ {BAUD_RATE}")
    print("=" * 65)

    try:
        connection = mavutil.mavlink_connection(serial_port, baud=BAUD_RATE)
    except Exception as e:
        print(f"ERROR opening {serial_port}: {e}")
        return

    print("Connecting and waiting for Pixhawk HEARTBEAT...")
    connection.wait_heartbeat()
    print("CONNECTED!")
    print(f"System: {connection.target_system} | Component: {connection.target_component}")
    print("\nSending synthetic LANDING_TARGET messages (x=0.0m, y=0.0m, z=1.0m)...")
    print("Press Ctrl+C to stop.\n")

    msg_count = 0
    start_time = time.time()

    while True:
        try:
            # Synthetic target directly 1.0m below the vehicle
            x = 0.0
            y = 0.0
            z = 1.0

            distance = math.sqrt(x*x + y*y + z*z)
            angle_x = math.atan2(x, z)
            angle_y = math.atan2(y, z)

            time_usec = int(time.time() * 1_000_000)

            # Transmit modern standard MAVLink LANDING_TARGET packet with positional coordinates
            connection.mav.landing_target_send(
                time_usec,
                0,                                     # target_num (0 for primary target)
                mavutil.mavlink.MAV_FRAME_LOCAL_NED,   # coordinate frame
                angle_x,                               # angle_x (radians)
                angle_y,                               # angle_y (radians)
                distance,                              # distance (meters)
                0.20,                                  # size_x (tag dimension in meters)
                0.20,                                  # size_y (tag dimension in meters)
                x,                                     # X target position in NED (meters)
                y,                                     # Y target position in NED (meters)
                z,                                     # Z target position in NED (meters)
                (1, 0, 0, 0),                          # Quaternion orientation (unit quaternion)
                mavutil.mavlink.LANDING_TARGET_TYPE_VISION_FIDUCIAL,  # Type 2: Visual fiducial
                1                                      # position_valid: 1 (CRITICAL for PX4)
            )

            msg_count += 1
            if msg_count % 10 == 0:
                elapsed = time.time() - start_time
                print(f"[TX] Sent {msg_count} pkts | Target: NED (x={x:.2f}, y={y:.2f}, z={z:.2f} m) | Dist={distance:.2f} m | Rate: {msg_count/elapsed:.1f} Hz")

            time.sleep(1.0 / RATE_HZ)

        except KeyboardInterrupt:
            print("\nStopped synthetic LANDING_TARGET transmission.")
            break

if __name__ == "__main__":
    main()
