import unittest

from src.mission.event_generator import MissionEventGenerator
from src.risk.risk_engine import RiskEngine
from src.situational_awareness.situational_state_builder import SituationalStateBuilder


class MissionEventGeneratorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.builder = SituationalStateBuilder()
        self.engine = RiskEngine()
        self.generator = MissionEventGenerator()

    def test_person_event(self) -> None:
        state = self.builder.build_state(1, 100, 25, 50, 5)
        events = self.generator.generate_events(state, self.engine.assess(state))
        self.assertIn("PERSON_DETECTED", [event.event_type for event in events])

    def test_critical_event(self) -> None:
        state = self.builder.build_state(1, 2500, 25, 50, 5)
        events = self.generator.generate_events(state, self.engine.assess(state))
        self.assertIn("CRITICAL_SITUATION", [event.event_type for event in events])

    def test_normal_event(self) -> None:
        state = self.builder.build_state(0, 100, 25, 50, 5)
        events = self.generator.generate_events(state, self.engine.assess(state))
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].event_type, "NORMAL_OPERATION")


if __name__ == "__main__":
    unittest.main()
