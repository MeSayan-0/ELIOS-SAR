from dataclasses import dataclass
from pathlib import Path
from typing import Any
import numpy as np
from ultralytics import YOLO


@dataclass
class PoseDetection:
    posture: str
    confidence: float
    keypoints: list
    bbox: list


class PoseEstimator:
    def __init__(
        self,
        model_path: str,
        confidence: float = 0.35,
        image_size: int = 320
    ):
        self.confidence = confidence
        self.image_size = image_size
        self.enabled = False
        self.model = None

        path = Path(model_path)

        if not path.is_absolute():
            cwd_path = Path.cwd() / path
            if cwd_path.exists():
                path = cwd_path
            else:
                path = Path(__file__).resolve().parents[2] / path

        self.model_path = path

        if not path.exists():
            print(
                f"[MODEL DISABLED] pose: {path.name} not found"
            )
            return

        try:
            self.model = YOLO(str(path))
            self.enabled = True
            print(
                f"[MODEL ENABLED] pose: {path}"
            )
        except Exception as exc:
            print(
                f"[MODEL DISABLED] pose: failed to load: {exc}"
            )

    def estimate(self, frame: Any) -> list[PoseDetection]:
        if not self.enabled or self.model is None or frame is None:
            return []

        results = self.model.predict(
            source=frame,
            conf=self.confidence,
            imgsz=self.image_size,
            device="cpu",
            verbose=False
        )

        output = []

        for result in results:
            if result.keypoints is None:
                continue

            boxes = result.boxes
            keypoints_data = result.keypoints.data

            if keypoints_data is None:
                continue

            keypoints_array = keypoints_data.cpu().numpy()

            for index, keypoints in enumerate(keypoints_array):
                bbox = []

                if boxes is not None and index < len(boxes):
                    bbox = boxes[index].xyxy[0].cpu().numpy().tolist()

                posture = self._classify_posture(keypoints)

                valid_conf = keypoints[:, 2]
                confidence = float(
                    np.mean(valid_conf[valid_conf > 0])
                ) if np.any(valid_conf > 0) else 0.0

                output.append(
                    PoseDetection(
                        posture=posture,
                        confidence=confidence,
                        keypoints=keypoints.tolist(),
                        bbox=[round(float(v), 2) for v in bbox]
                    )
                )

        return output

    def _classify_posture(self, keypoints: np.ndarray) -> str:
        visible = keypoints[:, 2] > 0.25

        if visible.sum() < 5:
            return "unknown"

        points = keypoints[visible][:, :2]

        min_x, min_y = points.min(axis=0)
        max_x, max_y = points.max(axis=0)

        width = max_x - min_x
        height = max_y - min_y

        if width > height * 1.25:
            return "lying"

        if height > width * 1.35:
            return "standing"

        return "crouching"
