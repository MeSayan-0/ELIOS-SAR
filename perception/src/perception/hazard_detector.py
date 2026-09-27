from src.perception.segmentation_detector import (
    SegmentationDetector,
    SegmentationDetection,
)

HazardDetection = SegmentationDetection


class HazardDetector(SegmentationDetector):
    def __init__(
        self,
        model_path: str,
        hazard_type: str,
        confidence: float = 0.30,
        image_size: int = 320
    ):
        super().__init__(
            model_path=model_path,
            hazard_type=hazard_type,
            confidence=confidence,
            image_size=image_size
        )
