import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from gcs.processor import GCSProcessor


processor = GCSProcessor()

packet = {
    "type": "ai_observation",
    "drone_id": "ELIOS-01",
    "timestamp": 1757920000.0,
    "frame_id": 100,
    "source": "ELIOS",

    "persons": [
        {
            "class": "rescuer",
            "confidence": 0.94,
            "bbox": [100, 100, 180, 300],
            "posture": "standing",
        }
    ],

    "hazards": {
        "fire": [],
        "flood": [
            {
                "class": "water",
                "confidence": 0.91,
                "area": 0.82,
                "severity": "critical",
                "bottom": True,
            }
        ],
        "boulder": [
            {
                "class": "rock",
                "confidence": 0.88,
                "area": 0.40,
                "severity": "high",
                "obstruction_level": "high",
            }
        ],
    },

    "drone_pose": {
        "frame": "mine_local",
        "x": 2.4,
        "y": 5.8,
        "z": 1.7,
        "roll": 0.01,
        "pitch": 0.02,
        "yaw": 1.2,
    },

    "sensors": {
        "gas_level": "normal",
    },

    "risk": {
        "level": "HIGH",
        "score": 50,
    },
}

result = processor.process(packet)

print("\n========== GCS RESULT ==========")
print(result)
print("=================================")
