import unittest

from src.fusion.sensor_fusion import SensorFusion


class IntelligenceIntegrationTests(unittest.TestCase):
    def test_person_in_gas_environment(self) -> None:
        rgb_output = {
            "persons": [
                {
                    "class_name": "person",
                    "confidence": 0.91,
                    "bbox": [100.0, 80.0, 200.0, 300.0],
                    "source": "rgb",
                }
            ],
            "hazards": [],
        }

        state = SensorFusion().build_state(
            person_detections=rgb_output["persons"],
            hazard_detections=rgb_output["hazards"],
            methane_level=0.65,
            temperature_c=31.0,
            humidity_percent=72.0,
            nearest_obstacle_m=1.8,
            position={"x_m": 4.2, "y_m": 2.7},
        )

        self.assertEqual(state["person_count"], 1)
        self.assertEqual(state["gas_status"], "WARNING")
        self.assertEqual(state["position"]["x_m"], 4.2)


if __name__ == "__main__":
    unittest.main()
