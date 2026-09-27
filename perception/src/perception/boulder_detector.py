from src.perception.segmentation_detector import (
    SegmentationDetector,
    SegmentationDetection,
)

BoulderDetection = SegmentationDetection


class BoulderDetector(SegmentationDetector):
    def __init__(
        self,
        model_path: str,
        confidence: float = 0.30,
        image_size: int = 320
    ):
        super().__init__(
            model_path=model_path,
            hazard_type="rock",
            confidence=confidence,
            image_size=image_size
        )
