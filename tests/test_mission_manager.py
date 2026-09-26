import unittest

from src.mission.mission_manager import (
    MissionManager,
    MISSION_CREATED,
    MISSION_ACTIVE,
    MISSION_COMPLETED,
    MISSION_CANCELLED,
)


class TestMissionManager(unittest.TestCase):

    def setUp(self):
        self.manager = MissionManager()

    def test_create_mission(self):

        mission = self.manager.create_mission(
            anchor="A",
            location=(4.0, 6.0),
            reason="PERSON_DETECTED",
            risk_level="HIGH",
        )

        self.assertEqual(mission.mission_id, "MISSION-001")
        self.assertEqual(mission.anchor, "A")
        self.assertEqual(mission.location, (4.0, 6.0))
        self.assertEqual(mission.reason, "PERSON_DETECTED")
        self.assertEqual(mission.risk_level, "HIGH")
        self.assertEqual(mission.status, MISSION_CREATED)

    def test_mission_ids_are_unique(self):

        mission_a = self.manager.create_mission(
            anchor="A",
            location=(1.0, 1.0),
            reason="PERSON_DETECTED",
            risk_level="HIGH",
        )

        mission_b = self.manager.create_mission(
            anchor="B",
            location=(2.0, 2.0),
            reason="GAS_ANOMALY",
            risk_level="CRITICAL",
        )

        self.assertEqual(mission_a.mission_id, "MISSION-001")
        self.assertEqual(mission_b.mission_id, "MISSION-002")

    def test_assign_drone(self):

        mission = self.manager.create_mission(
            anchor="A",
            location=(1.0, 1.0),
            reason="PERSON_DETECTED",
            risk_level="HIGH",
        )

        result = self.manager.assign_drone(
            mission.mission_id,
            "D01",
        )

        self.assertTrue(result)
        self.assertEqual(mission.drone_id, "D01")

    def test_cannot_start_without_drone(self):

        mission = self.manager.create_mission(
            anchor="A",
            location=(1.0, 1.0),
            reason="PERSON_DETECTED",
            risk_level="HIGH",
        )

        result = self.manager.start_mission(
            mission.mission_id,
        )

        self.assertFalse(result)
        self.assertEqual(mission.status, MISSION_CREATED)

    def test_start_mission(self):

        mission = self.manager.create_mission(
            anchor="A",
            location=(1.0, 1.0),
            reason="PERSON_DETECTED",
            risk_level="HIGH",
        )

        self.manager.assign_drone(
            mission.mission_id,
            "D01",
        )

        result = self.manager.start_mission(
            mission.mission_id,
        )

        self.assertTrue(result)
        self.assertEqual(mission.status, MISSION_ACTIVE)
        self.assertIsNotNone(mission.started_at)

    def test_complete_mission(self):

        mission = self.manager.create_mission(
            anchor="A",
            location=(1.0, 1.0),
            reason="PERSON_DETECTED",
            risk_level="HIGH",
        )

        self.manager.assign_drone(
            mission.mission_id,
            "D01",
        )

        self.manager.start_mission(
            mission.mission_id,
        )

        result = self.manager.complete_mission(
            mission.mission_id,
        )

        self.assertTrue(result)
        self.assertEqual(mission.status, MISSION_COMPLETED)
        self.assertIsNotNone(mission.completed_at)

    def test_cancel_mission(self):

        mission = self.manager.create_mission(
            anchor="A",
            location=(1.0, 1.0),
            reason="GAS_ANOMALY",
            risk_level="CRITICAL",
        )

        result = self.manager.cancel_mission(
            mission.mission_id,
        )

        self.assertTrue(result)
        self.assertEqual(mission.status, MISSION_CANCELLED)

    def test_active_missions(self):

        mission_a = self.manager.create_mission(
            anchor="A",
            location=(1.0, 1.0),
            reason="PERSON_DETECTED",
            risk_level="HIGH",
        )

        mission_b = self.manager.create_mission(
            anchor="B",
            location=(2.0, 2.0),
            reason="GAS_ANOMALY",
            risk_level="CRITICAL",
        )

        self.manager.assign_drone(mission_a.mission_id, "D01")
        self.manager.assign_drone(mission_b.mission_id, "D01")

        self.manager.start_mission(mission_a.mission_id)
        self.manager.start_mission(mission_b.mission_id)

        active = self.manager.get_active_missions()

        self.assertEqual(len(active), 2)

    def test_add_note(self):

        mission = self.manager.create_mission(
            anchor="A",
            location=(1.0, 1.0),
            reason="PERSON_DETECTED",
            risk_level="HIGH",
        )

        result = self.manager.add_note(
            mission.mission_id,
            "Person located near tunnel obstruction.",
        )

        self.assertTrue(result)

        self.assertEqual(
            mission.notes[0],
            "Person located near tunnel obstruction.",
        )


if __name__ == "__main__":
    unittest.main()
