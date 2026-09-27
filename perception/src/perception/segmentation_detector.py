from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from ultralytics import YOLO


@dataclass
class SegmentationDetection:
    hazard_type: str
    class_name: str
    confidence: float
    bbox: list
    mask_area_ratio: float
    mask: Any = None
    touches_bottom: bool = False
    central_corridor_overlap: bool = False
    severity: str = "low"

    @property
    def obstruction_level(self):
        return self.severity


class SegmentationDetector:
    def __init__(
        self,
        model_path,
        hazard_type,
        confidence=0.30,
        image_size=320
    ):
        self.hazard_type = hazard_type
        self.confidence = confidence
        self.image_size = image_size
        self.enabled = False
        self.model = None

        model_path = Path(model_path)

        if not model_path.is_absolute():
            model_path = Path.cwd() / model_path

        self.model_path = model_path

        if not model_path.exists():
            print(
                f"[MODEL DISABLED] {hazard_type}: "
                f"{model_path.name} not found"
            )
            return

        try:
            self.model = YOLO(str(model_path))
            self.enabled = True

            print(
                f"[MODEL ENABLED] {hazard_type}: "
                f"{model_path} | Classes: {self.model.names}"
            )

        except Exception as exc:
            print(
                f"[MODEL DISABLED] {hazard_type}: "
                f"failed to load: {exc}"
            )

    def detect(self, frame):
        if not self.enabled or self.model is None:
            return []

        if frame is None:
            return []

        height, width = frame.shape[:2]

        results = self.model.predict(
            frame,
            conf=self.confidence,
            imgsz=self.image_size,
            device="cpu",
            verbose=False
        )

        detections = []

        for result in results:
            if result.boxes is None:
                continue

            masks_data = None

            if result.masks is not None:
                masks_data = result.masks.data

            for index, box in enumerate(result.boxes):

                confidence = float(
                    box.conf[0].item()
                )

                class_id = int(
                    box.cls[0].item()
                )

                class_name = self.model.names.get(
                    class_id,
                    str(class_id)
                )

                x1, y1, x2, y2 = (
                    box.xyxy[0]
                    .cpu()
                    .numpy()
                    .astype(int)
                    .tolist()
                )

                x1 = max(0, min(x1, width - 1))
                y1 = max(0, min(y1, height - 1))
                x2 = max(0, min(x2, width - 1))
                y2 = max(0, min(y2, height - 1))

                mask = None
                area_ratio = 0.0

                if masks_data is not None:
                    raw_mask = (
                        masks_data[index]
                        .cpu()
                        .numpy()
                    )

                    mask = cv2.resize(
                        raw_mask,
                        (width, height),
                        interpolation=cv2.INTER_NEAREST
                    ) > 0.5

                    area_ratio = float(
                        np.count_nonzero(mask)
                        / (width * height)
                    )

                touches_bottom = (
                    y2 >= int(height * 0.90)
                )

                corridor_left = int(width * 0.25)
                corridor_right = int(width * 0.75)

                central_corridor_overlap = (
                    x2 >= corridor_left and
                    x1 <= corridor_right and
                    y2 >= int(height * 0.35)
                )

                severity = self._calculate_severity(
                    area_ratio=area_ratio,
                    touches_bottom=touches_bottom,
                    central_corridor_overlap=(
                        central_corridor_overlap
                    )
                )

                detections.append(
                    SegmentationDetection(
                        hazard_type=self.hazard_type,
                        class_name=class_name,
                        confidence=round(
                            confidence,
                            4
                        ),
                        bbox=[
                            x1,
                            y1,
                            x2,
                            y2
                        ],
                        mask_area_ratio=round(
                            area_ratio,
                            5
                        ),
                        mask=mask,
                        touches_bottom=touches_bottom,
                        central_corridor_overlap=(
                            central_corridor_overlap
                        ),
                        severity=severity
                    )
                )

        return detections

    def _calculate_severity(
        self,
        area_ratio,
        touches_bottom,
        central_corridor_overlap
    ):
        if self.hazard_type == "flood":

            if area_ratio >= 0.35 and touches_bottom:
                return "critical"

            if area_ratio >= 0.18 and touches_bottom:
                return "high"

            if area_ratio >= 0.08:
                return "medium"

            return "low"

        if self.hazard_type == "rock":

            if area_ratio >= 0.10:
                return "critical"

            if area_ratio >= 0.04 and (
                central_corridor_overlap
            ):
                return "high"

            if central_corridor_overlap:
                return "medium"

            return "low"

        return "low"
