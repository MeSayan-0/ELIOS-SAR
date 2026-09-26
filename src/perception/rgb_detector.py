"""CPU RGB YOLO adapter for ELIOS-SAR's standard perception messages."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from src.utils.messages import HazardDetection, PersonDetection


# Keep Ultralytics settings inside the project rather than a user-profile path.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault("YOLO_CONFIG_DIR", str(PROJECT_ROOT))

from ultralytics import YOLO  # noqa: E402  (environment is configured above)


class RGBDetector:
    """Adapt a procured RGB YOLO detector to ELIOS-SAR message contracts.

    The currently procured model labels ``civilian`` and ``rescuer`` as human
    classes.  Its animal labels are retained in :meth:`get_class_names` but
    are not treated as hazards: no hazard semantics are inferred from an
    object label alone.
    """

    PERSON_CLASS_NAMES = frozenset({"person", "human", "civilian", "rescuer"})

    def __init__(self, model_path: str | Path, confidence_threshold: float = 0.25):
        self.model_path = Path(model_path)
        if not self.model_path.is_file():
            raise FileNotFoundError(
                f"RGB model file was not found: {self.model_path}. "
                "Expected models/rgb/rgb_disaster.pt."
            )
        if not 0.0 <= confidence_threshold <= 1.0:
            raise ValueError("confidence_threshold must be between 0.0 and 1.0")

        self.confidence_threshold = confidence_threshold
        self.model = YOLO(str(self.model_path))
        self._class_names = self._normalise_class_names(self.model.names)

    @staticmethod
    def _normalise_class_names(names: Any) -> dict[int, str]:
        """Return Ultralytics class metadata as an integer-keyed dictionary."""
        if isinstance(names, dict):
            return {int(class_id): str(name) for class_id, name in names.items()}
        return {class_id: str(name) for class_id, name in enumerate(names)}

    def get_class_names(self) -> dict[int, str]:
        """Return the class names embedded in the loaded checkpoint."""
        return dict(self._class_names)

    def detect(self, frame: Any) -> dict[str, list[PersonDetection] | list[HazardDetection]]:
        """Run CPU inference and return ELIOS-SAR person and hazard messages.

        ``frame`` is an OpenCV/Numpy image.  Unknown non-person object labels
        are intentionally omitted from ``hazards`` until a real hazard model
        or an approved class-mapping policy is introduced.
        """
        if frame is None:
            raise ValueError("Input frame is None")

        results = self.model.predict(
            source=frame,
            conf=self.confidence_threshold,
            device="cpu",
            verbose=False,
        )

        persons: list[PersonDetection] = []
        hazards: list[HazardDetection] = []
        detection_id = 1

        for result in results:
            if result.boxes is None:
                continue

            for box in result.boxes:
                class_id = int(box.cls[0])
                class_name = self._class_names[class_id]
                confidence = float(box.conf[0])
                bbox = [float(value) for value in box.xyxy[0].tolist()]

                if class_name.casefold() in self.PERSON_CLASS_NAMES:
                    persons.append(
                        PersonDetection(
                            id=detection_id,
                            confidence=confidence,
                            bbox=bbox,
                        )
                    )
                    detection_id += 1

        return {"persons": persons, "hazards": hazards}
