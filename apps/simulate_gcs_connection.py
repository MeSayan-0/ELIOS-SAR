import argparse
import json
import os
import sys
import time
import urllib.request

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.communication.drone_link import DroneLink
from src.simulation.lidar_simulator import LidarSimulator, TunnelEnvironment
from src.mapping.occupancy_map import OccupancyGrid


class HttpDroneTransport:
    """
    HTTP transport that forwards DroneLink serialized JSON messages
    to the ELIOS-SAR GCS backend.
    """

    def __init__(
        self,
        endpoint_url: str = "http://127.0.0.1:8000/api/message",
    ) -> None:
        self.endpoint_url = endpoint_url
        self.connected = False

    def connect(self) -> None:
        self.connected = True

    def disconnect(self) -> None:
        self.connected = False

    def send(self, serialized_message: str) -> None:
        if not self.connected:
            raise ConnectionError("HTTP transport is not connected.")

        data = json.loads(serialized_message)
        payload_bytes = json.dumps(data).encode("utf-8")

        req = urllib.request.Request(
            self.endpoint_url,
            data=payload_bytes,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status != 200:
                raise RuntimeError(
                    f"GCS backend responded with HTTP {response.status}"
                )


def run_simulation(
    endpoint: str = "http://127.0.0.1:8000/api/message",
    once: bool = False,
    steps: int = 1,
) -> None:
    print(f"Connecting DroneLink to GCS backend at {endpoint}...")

    transport = HttpDroneTransport(endpoint_url=endpoint)
    drone = DroneLink(
        drone_id="DRONE-01",
        transport=transport,
    )
    drone.connect()

    environment = TunnelEnvironment(
        min_x=-4.0,
        max_x=4.0,
        min_y=-3.0,
        max_y=3.0,
    )
    lidar = LidarSimulator()
    grid = OccupancyGrid(width=100, height=100, resolution=0.1)

    step_count = 0

    while True:
        step_count += 1
        pos_x = 2.40 + (step_count * 0.05)
        pos_y = 1.10 + (step_count * 0.02)
        alt = 3.00
        battery = max(20.0, 87.5 - (step_count * 0.1))

        print(f"[{step_count}] Sending DRONE_STATE...")
        drone.send_drone_state(
            position={
                "x": round(pos_x, 2),
                "y": round(pos_y, 2),
                "z": round(alt, 2),
            },
            battery=round(battery, 1),
            armed=True,
            flight_mode="RECON",
        )

        print(f"[{step_count}] Sending SENSOR_STATE...")
        drone.send_sensor_state(
            gas={"methane_ppm": 120.0},
            temperature=26.5,
            humidity=68.0,
        )

        print(f"[{step_count}] Sending PERSON_DETECTION...")
        drone.send_person_detection(
            person_id="PERSON-01",
            position={
                "x": round(pos_x, 2),
                "y": round(pos_y, 2),
                "z": 0.0,
            },
            confidence=0.94,
        )

        print(f"[{step_count}] Sending HAZARD...")
        drone.send_hazard(
            hazard_type="METHANE",
            position={
                "x": round(pos_x + 0.6, 2),
                "y": round(pos_y + 0.4, 2),
                "z": 0.0,
            },
            severity="MEDIUM",
            confidence=0.91,
        )

        print(f"[{step_count}] Sending RISK_EVENT...")
        drone.send_risk_event(
            risk_level="HIGH",
            score=82.0,
            affected_person_id="PERSON-01",
            reason="Survivor detected near methane pocket",
        )

        print(f"[{step_count}] Sending MISSION_EVENT...")
        drone.send_mission_event(
            mission_id="MISSION-001",
            event_type="SURVIVOR_FOUND",
            description="Survivor confirmed at anchor waypoint",
        )

        scan_measurements = lidar.scan(
            drone_x=pos_x,
            drone_y=pos_y,
            drone_yaw=0.0,
            environment=environment,
        )
        grid.update_scan(robot_x=pos_x, robot_y=pos_y, measurements=scan_measurements)

        print(f"[{step_count}] Sending MAP_UPDATE...")
        drone.send_map_update(
            drone_position={
                "x": round(pos_x, 2),
                "y": round(pos_y, 2),
                "z": round(alt, 2),
            },
            map_data=grid.grid,
        )

        if once or step_count >= steps:
            print("Completed requested simulation steps.")
            break

        time.sleep(1.0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Simulate ELIOS-SAR Drone to GCS bridge"
    )
    parser.add_argument(
        "--endpoint",
        type=str,
        default="http://127.0.0.1:8000/api/message",
        help="GCS backend message endpoint",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Send one burst and exit",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=1,
        help="Number of steps to send (default: 1)",
    )
    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Run continuously until interrupted",
    )

    args = parser.parse_args()

    run_once = args.once or (not args.continuous and args.steps == 1)
    target_steps = 999999 if args.continuous else args.steps

    run_simulation(
        endpoint=args.endpoint,
        once=run_once,
        steps=target_steps,
    )
