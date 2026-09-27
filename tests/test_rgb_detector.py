"""Integration tests for the real procured RGB YOLO model adapter."""

from pathlib import Path
import unittest

import numpy as np

from src.perception.rgb_detector import RGBDetector
from src.utils.messages import HazardDetection, PersonDetection


MODEL_PATH = Path("models/rgb/rgb_disaster.pt")


class RGBDetectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not MODEL_PATH.is_file():
            raise FileNotFoundError(
                f"RGB model is required for this integration test: {MODEL_PATH}"
            )
        cls.detector = RGBDetector(MODEL_PATH)

    def test_missing_model_path_has_clear_error(self) -> None:
        with self.assertRaisesRegex(FileNotFoundError, "RGB model file was not found"):
            RGBDetector("models/rgb/missing_model.pt")

    def test_class_names_are_retrieved_from_checkpoint(self) -> None:
        class_names = self.detector.get_class_names()

        self.assertEqual(len(class_names), 6)
        self.assertEqual(class_names[1], "civilian")
        self.assertEqual(class_names[5], "rescuer")

    def test_real_inference_returns_standard_structure(self) -> None:
        frame = np.zeros((64, 64, 3), dtype=np.uint8)
        detections = self.detector.detect(frame)

        self.assertEqual(set(detections), {"persons", "hazards"})
        self.assertIsInstance(detections["persons"], list)
        self.assertIsInstance(detections["hazards"], list)

        for detection in detections["persons"]:
            self.assertIsInstance(detection, PersonDetection)
            self.assertGreaterEqual(detection.confidence, 0.0)
            self.assertLessEqual(detection.confidence, 1.0)
            self.assertEqual(len(detection.bbox), 4)

        for detection in detections["hazards"]:
            self.assertIsInstance(detection, HazardDetection)
            self.assertGreaterEqual(detection.confidence, 0.0)
            self.assertLessEqual(detection.confidence, 1.0)
            self.assertEqual(len(detection.bbox), 4)


if __name__ == "__main__":
    unittest.main()
