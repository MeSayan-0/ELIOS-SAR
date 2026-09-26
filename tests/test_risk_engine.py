import unittest

from src.risk.risk_engine import RiskEngine
from src.situational_awareness.situational_state_builder import SituationalStateBuilder


class RiskEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.builder = SituationalStateBuilder()
        self.engine = RiskEngine()

    def test_normal_environment(self) -> None:
        state = self.builder.build_state(0, 100, 25, 50, 5)
        self.assertEqual(self.engine.assess(state).overall_risk, "LOW")

    def test_single_person(self) -> None:
        state = self.builder.build_state(1, 100, 25, 50, 5)
        assessment = self.engine.assess(state)
        self.assertIn(assessment.person_risk, ["LOW", "MEDIUM", "HIGH"])
        self.assertEqual(assessment.isolation_risk, "HIGH")

    def test_person_with_gas_warning(self) -> None:
        state = self.builder.build_state(1, 1500, 25, 50, 5)
        assessment = self.engine.assess(state)
        self.assertEqual(assessment.person_risk, "HIGH")
        self.assertIn(assessment.overall_risk, ["HIGH", "CRITICAL"])

    def test_person_with_critical_gas(self) -> None:
        state = self.builder.build_state(1, 2500, 25, 50, 5)
        assessment = self.engine.assess(state)
        self.assertEqual(assessment.person_risk, "CRITICAL")
        self.assertEqual(assessment.overall_risk, "CRITICAL")
        self.assertGreaterEqual(assessment.priority_score, 90)

    def test_multiple_environmental_warnings(self) -> None:
        state = self.builder.build_state(0, 1500, 45, 90, 5)
        assessment = self.engine.assess(state)
        self.assertEqual(assessment.environmental_risk, "CRITICAL")

    def test_explanation_exists(self) -> None:
        state = self.builder.build_state(1, 1500, 25, 50, 5)
        self.assertTrue(self.engine.assess(state).explanation)


if __name__ == "__main__":
    unittest.main()
