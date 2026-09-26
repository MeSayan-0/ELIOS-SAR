import unittest

from src.situational_awareness.situational_state_builder import (
    SituationalStateBuilder,
)


class SituationalStateBuilderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.builder = SituationalStateBuilder()

    def test_person_detection(self) -> None:
        state = self.builder.build_state(person_count=2)
        self.assertTrue(state.person_present)
        self.assertEqual(state.person_count, 2)

    def test_no_person(self) -> None:
        state = self.builder.build_state(person_count=0)
        self.assertFalse(state.person_present)
        self.assertEqual(state.person_count, 0)

    def test_gas_warning(self) -> None:
        state = self.builder.build_state(methane_ppm=1500)
        self.assertEqual(state.gas_status, "WARNING")
        self.assertEqual(state.overall_state, "HAZARDOUS")

    def test_gas_critical(self) -> None:
        state = self.builder.build_state(methane_ppm=2500)
        self.assertEqual(state.gas_status, "CRITICAL")
        self.assertEqual(state.overall_state, "CRITICAL")

    def test_temperature_warning(self) -> None:
        state = self.builder.build_state(temperature_c=45)
        self.assertEqual(state.temperature_status, "WARNING")

    def test_humidity_warning(self) -> None:
        state = self.builder.build_state(humidity_percent=90)
        self.assertEqual(state.humidity_status, "WARNING")

    def test_obstacle_warning(self) -> None:
        state = self.builder.build_state(nearest_obstacle_distance=1.0)
        self.assertEqual(state.obstacle_status, "WARNING")

    def test_normal_environment(self) -> None:
        state = self.builder.build_state(
            methane_ppm=100,
            temperature_c=25,
            humidity_percent=50,
            nearest_obstacle_distance=5,
        )
        self.assertEqual(state.overall_state, "NORMAL")

    def test_unknown_environment(self) -> None:
        state = self.builder.build_state(person_count=0)
        self.assertEqual(state.gas_status, "UNKNOWN")
        self.assertEqual(state.temperature_status, "UNKNOWN")
        self.assertEqual(state.humidity_status, "UNKNOWN")
        self.assertEqual(state.obstacle_status, "UNKNOWN")
        self.assertEqual(state.overall_state, "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
