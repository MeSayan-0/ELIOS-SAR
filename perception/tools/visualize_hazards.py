import cv2
import time
import os
import sys
from ultralytics import YOLO

VIDEO_PATH = "test.mp4"

rock_model = YOLO("models/hazards/boulder.pt")
flood_model = YOLO("models/hazards/flood.pt")

cap = cv2.VideoCapture(VIDEO_PATH)

fps = cap.get(cv2.CAP_PROP_FPS)
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

writer = cv2.VideoWriter(
    "hazard_visualization.mp4",
    cv2.VideoWriter_fourcc(*"mp4v"),
    fps if fps > 0 else 15,
    (width, height)
)

frame_index = 0
max_frames = 300

print(f"[VISUALIZE] Generating hazard_visualization.mp4 for {max_frames} frames...")

while True:
    ok, frame = cap.read()

    if not ok:
        break

    rock_result = rock_model.predict(
        frame,
        conf=0.20,
        imgsz=320,
        device="cpu",
        verbose=False
    )[0]

    flood_result = flood_model.predict(
        frame,
        conf=0.20,
        imgsz=320,
        device="cpu",
        verbose=False
    )[0]

    annotated = frame.copy()

    if rock_result.masks is not None:
        annotated = rock_result.plot(img=annotated)

    if flood_result.masks is not None:
        annotated = flood_result.plot(img=annotated)

    cv2.putText(
        annotated,
        f"Frame: {frame_index}",
        (20, 35),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (255, 255, 255),
        2
    )

    writer.write(annotated)

    try:
        cv2.imshow("Hazard Visualization", annotated)
        if cv2.waitKey(1) & 0xFF == 27:
            break
    except Exception:
        pass

    frame_index += 1

    if frame_index >= max_frames:
        print(f"[VISUALIZE] Finished {max_frames} frames.")
        break

cap.release()
writer.release()
try:
    cv2.destroyAllWindows()
except Exception:
    pass

print(f"[VISUALIZE] Output saved to: {os.path.abspath('hazard_visualization.mp4')}")
