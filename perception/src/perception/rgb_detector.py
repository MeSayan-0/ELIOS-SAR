from __future__ import annotations

from pathlib import Path
from typing import Any

from ultralytics import YOLO


class RGBDetector:
    def __init__(
        self,
        model_path: str,
        confidence: float = 0.40,
    ) -> None:
        path = Path(model_path)

        if not path.is_absolute():
            path = Path(__file__).resolve().parents[2] / path

        if not path.exists():
            raise FileNotFoundError(
                f"RGB model not found: {path}"
            )

        self.model = YOLO(str(path))
        self.confidence = confidence

    def detect(
        self,
        frame,
    ) -> list[dict[str, Any]]:

        if frame is None:
            return []

        results = self.model.predict(
            source=frame,
            conf=self.confidence,
            device="cpu",
            verbose=False,
        )

        detections: list[dict[str, Any]] = []

        for result in results:

            if result.boxes is None:
                continue

            names = result.names

            for box in result.boxes:

                class_id = int(
                    box.cls[0]
                )

                confidence = float(
                    box.conf[0]
                )

                raw_label = str(
                    names[class_id]
                ).lower()

                # Supported human/victim classes
                if raw_label not in ("person", "civilian", "rescuer", "human"):
                    continue

                label = raw_label

                x1, y1, x2, y2 = (
                    box.xyxy[0].tolist()
                )

                detections.append(
                    {
                        "label": label,

                        "confidence": confidence,

                        "bbox": [
                            float(x1),
                            float(y1),
                            float(x2),
                            float(y2),
                        ],
                    }
                )

        return detections
