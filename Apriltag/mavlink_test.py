import sys
import glob
import time
from pymavlink import mavutil

DEFAULT_PORTS = ["/dev/serial0", "/dev/ttyAMA0", "/dev/ttyUSB0", "/dev/ttyACM0"]
BAUD_RATE = 57600

def find_serial_port():
    if len(sys.argv) > 1:
        return sys.argv[1]
    for p in DEFAULT_PORTS:
        if glob.glob(p):
            return p
    return "/dev/serial0"

def main():
    serial_port = find_serial_port()
    print("=" * 60)
    print("ELIOS-SAR MAVLink Telemetry Check (Stage 3)")
    print("=" * 60)
    print(f"Connecting to Pixhawk on {serial_port} @ {BAUD_RATE} baud...")
    print("Waiting for HEARTBEAT from Pixhawk (Ensure Pixhawk is powered on and TELEM2 TX/RX crossed)...")
    print("Press Ctrl+C to stop.")
    print("-" * 60)

    try:
        connection = mavutil.mavlink_connection(serial_port, baud=BAUD_RATE)
    except Exception as e:
        print(f"ERROR opening {serial_port}: {e}")
        return

    # Wait for heartbeat with a 15-second reminder
    start_time = time.time()
    heartbeat_received = False

    while not heartbeat_received:
        msg = connection.wait_heartbeat(timeout=3)
        if msg:
            heartbeat_received = True
            break
        elapsed = int(time.time() - start_time)
        print(f"[{elapsed}s] Still waiting for HEARTBEAT on {serial_port}...")
        if elapsed >= 30:
            print("\nTROUBLESHOOTING:")
            print("1. Verify physical TX/RX wires are crossed (Pi TX -> Pixhawk RX, Pi RX -> Pixhawk TX).")
            print("2. Verify common GND is connected.")
            print("3. In QGroundControl, verify MAV_1_CONFIG is set to TELEM2 and SER_TEL2_BAUD is 57600.")
            print("4. Check 'ls -l /dev/serial0' on the Pi.")
            break

    if not heartbeat_received:
        return

    print()
    print("=" * 60)
    print("PIXHAWK CONNECTED!")
    print("=" * 60)
    print(f"Target System ID:    {connection.target_system}")
    print(f"Target Component ID: {connection.target_component}")
    print(f"Vehicle Type:        {msg.type}")
    print(f"Autopilot:           {msg.autopilot}")
    print(f"Base Mode:           {bin(msg.base_mode)}")
    print("=" * 60)
    print("Streaming live telemetry packets (ATTITUDE, VFR_HUD, SYS_STATUS)...")
    print()

    packet_count = 0
    while True:
        try:
            msg = connection.recv_match(blocking=True, timeout=2.0)
            if msg is None:
                continue

            msg_type = msg.get_type()
            if msg_type in ["ATTITUDE", "GLOBAL_POSITION_INT", "SYS_STATUS", "VFR_HUD", "HEARTBEAT"]:
                packet_count += 1
                if msg_type == "ATTITUDE":
                    print(f"[ATTITUDE] Roll={msg.roll * 57.2958:+.1f} deg, Pitch={msg.pitch * 57.2958:+.1f} deg, Yaw={msg.yaw * 57.2958:+.1f} deg")
                elif msg_type == "VFR_HUD":
                    print(f"[VFR_HUD] Heading={msg.heading} deg, Alt={msg.alt:.1f} m, Airspeed={msg.airspeed:.1f} m/s")
                elif msg_type == "HEARTBEAT":
                    print(f"[HEARTBEAT] System {connection.target_system} active")
        except KeyboardInterrupt:
            print("\nExiting telemetry check.")
            break

if __name__ == "__main__":
    main()
