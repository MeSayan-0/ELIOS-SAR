import asyncio
import base64
import json
import time

import cv2
import numpy as np
import websockets


GCS_HOST = "127.0.0.1"
VIDEO_PORT = 8766
DETECTION_PORT = 8767


def create_test_frame(frame_id):

    frame = np.zeros(
        (480, 640, 3),
        dtype=np.uint8,
    )

    frame[:] = (40, 40, 40)

    # Fake person-like rectangle
    x1, y1, x2, y2 = 180, 100, 350, 400

    cv2.rectangle(
        frame,
        (x1, y1),
        (x2, y2),
        (0, 255, 0),
        2,
    )

    cv2.putText(
        frame,
        f"RAW TEST FRAME {frame_id}",
        (20, 450),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2,
    )

    return frame


async def send_test_data():

    video_uri = f"ws://{GCS_HOST}:{VIDEO_PORT}"
    detection_uri = f"ws://{GCS_HOST}:{DETECTION_PORT}"

    async with websockets.connect(
        video_uri,
        max_size=8 * 1024 * 1024,
    ) as video_ws, websockets.connect(
        detection_uri,
        max_size=2 * 1024 * 1024,
    ) as detection_ws:

        print("[TEST] Connected to GCS")

        for frame_id in range(1, 500):

            frame = create_test_frame(frame_id)

            success, encoded = cv2.imencode(
                ".jpg",
                frame,
                [
                    cv2.IMWRITE_JPEG_QUALITY,
                    80,
                ],
            )

            if not success:
                continue

            jpeg_bytes = encoded.tobytes()

            video_packet = {
                "frame_id": frame_id,
                "timestamp": time.time(),
                "jpeg_data": base64.b64encode(
                    jpeg_bytes
                ).decode("ascii"),
            }

            detection_packet = {
                "frame_id": frame_id,
                "timestamp": time.time(),
                "detections": [
                    {
                        "class_name": "person",
                        "confidence": 0.94,
                        "bbox": [180, 100, 350, 400],
                        "track_id": 1,
                    }
                ],
                "risk_level": "HIGH",
                "risk_score": 75,
            }

            await video_ws.send(
                json.dumps(video_packet)
            )

            await detection_ws.send(
                json.dumps(detection_packet)
            )

            await asyncio.sleep(0.05)

        print("[TEST] Finished sending frames")


if __name__ == "__main__":
    asyncio.run(send_test_data())
