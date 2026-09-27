import asyncio
import os
import sys
import logging

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import websockets
from gcs.receiver import GCSReceiver
from src.communication.telemetry_sender import TelemetrySender
from src.telemetry.observation_serializer import ObservationSerializer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)


async def main():
    print("=== STARTING END-TO-END TELEMETRY TEST ===")

    receiver = GCSReceiver(host="127.0.0.1", port=8766)
    server = await websockets.serve(
        receiver.handler,
        receiver.host,
        receiver.port,
        ping_interval=20,
        ping_timeout=20,
        max_size=4 * 1024 * 1024,
    )
    print("GCS Receiver started on ws://127.0.0.1:8766")

    sender = TelemetrySender(gcs_host="127.0.0.1", port=8766)
    serializer = ObservationSerializer(drone_id="ELIOS-01")

    # Packet 1: Normal rescuer observation
    packet1 = serializer.build(
        persons=[
            {
                "class": "rescuer",
                "confidence": 0.95,
                "bbox": [100, 100, 200, 300],
                "posture": "standing",
            }
        ],
        hazards={"fire": [], "flood": [], "boulder": []},
        drone_pose={"frame": "mine_local", "x": 1.0, "y": 2.0, "z": 0.5},
        sensors={"gas_level": "normal"},
        risk={"level": "LOW", "score": 20, "reasons": ["person_detected"]},
    )

    success1 = await sender.send(packet1)
    print(f"Packet 1 sent: {success1}")

    # Packet 2: Critical flood hazard observation
    packet2 = serializer.build(
        persons=[],
        hazards={
            "fire": [],
            "flood": [
                {
                    "class": "water",
                    "confidence": 0.91,
                    "severity": "critical",
                    "area": 0.85,
                    "bottom": True,
                }
            ],
            "boulder": [],
        },
        drone_pose={"frame": "mine_local", "x": 1.5, "y": 2.5, "z": 0.5},
        sensors={"gas_level": "normal"},
        risk={"level": "HIGH", "score": 80, "reasons": ["flood_detected"]},
    )

    success2 = await sender.send(packet2)
    print(f"Packet 2 sent: {success2}")

    # Give receiver time to process
    await asyncio.sleep(1.0)

    # Cleanup
    await sender.close()
    server.close()
    await server.wait_closed()

    print("=== END-TO-END TELEMETRY TEST COMPLETED SUCCESSFULLY ===")


if __name__ == "__main__":
    asyncio.run(main())
