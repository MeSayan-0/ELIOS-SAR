"""Run the ELIOS-SAR RGB detector on a video and display detections."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

import cv2

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.perception.rgb_detector import RGBDetector


DEFAULT_MODEL_PATH = Path("models/rgb/rgb_disaster.pt")


def draw_detections(frame: Any, output: dict[str, list[Any]]) -> Any:
    """Draw standard detector messages on an OpenCV frame."""
    person_count = len(output["persons"])

    for index, detection in enumerate(output["persons"], start=1):
        x1, y1, x2, y2 = map(int, detection.bbox)
        label = f"Person {index} {detection.confidence:.2f}"
        color = (0, 255, 0)

        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(
            frame,
            label,
            (x1, max(y1 - 10, 20)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            color,
            2,
        )

    for detection in output["hazards"]:
        x1, y1, x2, y2 = map(int, detection.bbox)
        label = f"{detection.hazard_type} {detection.confidence:.2f}"
        color = (0, 0, 255)

        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(
            frame,
            label,
            (x1, max(y1 - 10, 20)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            color,
            2,
        )

    cv2.putText(
        frame,
        f"Persons: {person_count}",
        (20, 35),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (255, 255, 255),
        2,
    )
    return frame


def run(video_path: str | Path, model_path: str | Path, confidence: float) -> None:
    """Run inference until the video ends or the user presses Q."""
    detector = RGBDetector(
        model_path=model_path,
        confidence_threshold=confidence,
    )

    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    print("ELIOS-SAR RGB detector running.")
    print("Press Q to exit.")

    try:
        while True:
            success, frame = capture.read()
            if not success:
                break

            output = detector.detect(frame)
            cv2.imshow(
                "ELIOS-SAR - RGB Perception",
                draw_detections(frame, output),
            )

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        capture.release()
        cv2.destroyAllWindows()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video", required=True, help="Input video path")
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL_PATH,
        help=f"RGB YOLO checkpoint (default: {DEFAULT_MODEL_PATH})",
    )
    parser.add_argument(
        "--confidence",
        type=float,
        default=0.40,
        help="Minimum detection confidence (default: 0.40)",
    )
    args = parser.parse_args()
    run(args.video, args.model, args.confidence)


if __name__ == "__main__":
    main()
