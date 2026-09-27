import asyncio
import os
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import cv2
import numpy as np

from src.communication.video_sender import VideoSender


async def main():

    sender = VideoSender(
        gcs_host="127.0.0.1",
        video_port=8766,
        detection_port=8767,
        jpeg_quality=75,
    )

    await sender.connect()

    for frame_id in range(1, 300):

        frame = np.zeros(
            (480, 640, 3),
            dtype=np.uint8,
        )

        frame[:] = (30, 30, 30)

        detections = [
            {
                "class_name": "person",
                "confidence": 0.91,
                "bbox": [150, 100, 360, 410],
                "track_id": 5,
            }
        ]

        cv2.putText(
            frame,
            "RAW VIDEO FROM ELIOS",
            (20, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2,
        )

        await sender.send(
            frame=frame,
            frame_id=frame_id,
            detections=detections,
            risk_level="HIGH",
            risk_score=65,
            timestamp=time.time(),
        )

        await asyncio.sleep(0.05)

    await sender.close()

    print("[TEST] Real VideoSender test complete")


if __name__ == "__main__":
    asyncio.run(main())
