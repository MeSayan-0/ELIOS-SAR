import asyncio
import base64
import json
import os
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import cv2
import numpy as np
import websockets

from gcs.annotation_renderer import AnnotationRenderer
from src.communication.video_sender import VideoSender


async def run_mock_gcs_receiver(received_data: dict, stop_event: asyncio.Event):
    renderer = AnnotationRenderer()

    async def video_handler(ws):
        async for msg in ws:
            packet = json.loads(msg)
            frame_id = packet["frame_id"]
            jpeg_bytes = base64.b64decode(packet["jpeg_data"])
            array = np.frombuffer(jpeg_bytes, dtype=np.uint8)
            frame = cv2.imdecode(array, cv2.IMREAD_COLOR)
            received_data["video_frames"].append((frame_id, frame.shape))

    async def detection_handler(ws):
        async for msg in ws:
            packet = json.loads(msg)
            received_data["detections"].append(packet["frame_id"])

    v_srv = await websockets.serve(video_handler, "127.0.0.1", 8766, max_size=8 * 1024 * 1024)
    d_srv = await websockets.serve(detection_handler, "127.0.0.1", 8767, max_size=2 * 1024 * 1024)

    await stop_event.wait()
    v_srv.close()
    d_srv.close()
    await v_srv.wait_closed()
    await d_srv.wait_closed()


async def main():
    print("=== STARTING VIDEO + DETECTION PIPELINE VERIFICATION ===")
    received_data = {"video_frames": [], "detections": []}
    stop_event = asyncio.Event()

    # Start mock GCS receiver
    receiver_task = asyncio.create_task(run_mock_gcs_receiver(received_data, stop_event))
    await asyncio.sleep(0.2)

    # Connect VideoSender
    sender = VideoSender(gcs_host="127.0.0.1", video_port=8766, detection_port=8767, jpeg_quality=70)
    await sender.connect()

    for frame_id in range(1, 15):
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        detections = [
            {"class_name": "person", "confidence": 0.92, "bbox": [100, 100, 200, 300], "track_id": 1},
            {"class_name": "water", "confidence": 0.88, "bbox": [0, 300, 640, 480], "track_id": None},
        ]
        await sender.send(
            frame=frame,
            frame_id=frame_id,
            detections=detections,
            risk_level="HIGH",
            risk_score=75,
            timestamp=time.time(),
        )
        await asyncio.sleep(0.02)

    await asyncio.sleep(0.5)
    await sender.close()
    stop_event.set()
    await receiver_task

    print(f"Verified: Received {len(received_data['video_frames'])} video frames and {len(received_data['detections'])} detection packets.")
    assert len(received_data["video_frames"]) >= 10
    assert len(received_data["detections"]) >= 10
    print("=== VIDEO PIPELINE VERIFICATION SUCCESSFUL ===")


if __name__ == "__main__":
    asyncio.run(main())
