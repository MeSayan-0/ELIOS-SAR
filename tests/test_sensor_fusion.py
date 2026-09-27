import unittest

from src.fusion.sensor_fusion import SensorFusion


class SensorFusionTests(unittest.TestCase):
    def test_normal_environment(self) -> None:
        state = SensorFusion().build_state(
            person_detections=[],
            hazard_detections=[],
            methane_level=0.20,
            temperature_c=27.0,
            humidity_percent=65.0,
            nearest_obstacle_m=2.5,
            position={"x_m": 0.0, "y_m": 0.0},
        )
        self.assertEqual(state["person_count"], 0)
        self.assertEqual(state["gas_status"], "NORMAL")
        self.assertEqual(state["obstacle_status"], "NORMAL")

    def test_gas_warning(self) -> None:
        state = SensorFusion().build_state([], [], 0.50, 30.0, 70.0, 2.0, None)
        self.assertEqual(state["gas_status"], "WARNING")

    def test_gas_critical(self) -> None:
        state = SensorFusion().build_state([], [], 0.80, 30.0, 70.0, 2.0, None)
        self.assertEqual(state["gas_status"], "CRITICAL")

    def test_missing_sensor_is_unknown(self) -> None:
        state = SensorFusion().build_state([], [], None, None, None, None, None)
        self.assertEqual(state["gas_status"], "UNKNOWN")
        self.assertEqual(state["obstacle_status"], "UNKNOWN")

    def test_hazard_types_accept_contract_objects(self) -> None:
        class Hazard:
            hazard_type = "gas"

        state = SensorFusion().build_state([], [Hazard()], None, None, None, None, None)
        self.assertEqual(state["hazard_types"], ["gas"])


if __name__ == "__main__":
    unittest.main()
