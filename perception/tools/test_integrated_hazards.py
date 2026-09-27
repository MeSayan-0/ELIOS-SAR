import os
import sys
import cv2
import json

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.perception.boulder_detector import BoulderDetector
from src.perception.hazard_detector import HazardDetector
from src.perception.risk_engine import RiskEngine
from src.core.risk_state import PersistentRiskState


VIDEO_PATH = "test.mp4"


rock_detector = BoulderDetector(
    model_path="models/hazards/boulder.pt",
    confidence=0.25,
    image_size=320
)

flood_detector = HazardDetector(
    model_path="models/hazards/flood.pt",
    hazard_type="flood",
    confidence=0.25,
    image_size=320
)

fire_detector = HazardDetector(
    model_path="models/hazards/fire.pt",
    hazard_type="fire",
    confidence=0.30,
    image_size=320
)

risk_engine = RiskEngine()
persistent_risk_state = PersistentRiskState()


cap = cv2.VideoCapture(VIDEO_PATH)

frame_index = 0

while True:
    ok, frame = cap.read()

    if not ok:
        break

    rock_results = rock_detector.detect(frame)
    flood_results = flood_detector.detect(frame)

    if rock_results or flood_results:
        print("\nFRAME:", frame_index)

        print(
            "ROCK:",
            [
                {
                    "class": d.class_name,
                    "confidence": d.confidence,
                    "area": d.mask_area_ratio,
                    "severity": d.severity,
                    "corridor": d.central_corridor_overlap
                }
                for d in rock_results
            ]
        )

        print(
            "FLOOD:",
            [
                {
                    "class": d.class_name,
                    "confidence": d.confidence,
                    "area": d.mask_area_ratio,
                    "severity": d.severity,
                    "bottom": d.touches_bottom
                }
                for d in flood_results
            ]
        )

        risk = risk_engine.evaluate(
            hazards={
                "boulder": rock_results,
                "flood": flood_results,
            }
        )
        persisted = persistent_risk_state.update(
            candidate_level=risk.level,
            candidate_score=risk.score,
            reasons=risk.reasons
        )

        print("RiskResult:", risk)
        print("PERSISTENT RISK:", persisted.level, f"(score={persisted.score})")

    frame_index += 1

    if frame_index >= 300:
        break

cap.release()
