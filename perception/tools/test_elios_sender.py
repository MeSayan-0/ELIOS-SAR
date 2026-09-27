import asyncio
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.communication.telemetry_sender import TelemetrySender
from src.telemetry.observation_serializer import ObservationSerializer


async def main():
    gcs_host = os.getenv(
        "GCS_HOST",
        "127.0.0.1",
    )

    sender = TelemetrySender(
        gcs_host=gcs_host,
        port=8766,
    )

    serializer = ObservationSerializer(
        drone_id="ELIOS-01"
    )

    packet = serializer.build(
        persons=[
            {
                "class": "rescuer",
                "confidence": 0.93,
                "bbox": [100, 100, 200, 300],
                "posture": "standing",
            }
        ],
        hazards={
            "fire": [],
            "flood": [
                {
                    "class": "water",
                    "confidence": 0.90,
                    "severity": "critical",
                    "area": 0.75,
                }
            ],
            "boulder": [],
        },
        drone_pose=None,
        sensors={
            "gas_level": "normal",
        },
        risk={
            "level": "HIGH",
            "score": 60,
            "reasons": ["flood_detected"],
        },
    )

    await sender.send(packet)

    print("Telemetry packet sent to GCS")

    await asyncio.sleep(1)
    await sender.close()


if __name__ == "__main__":
    asyncio.run(main())
