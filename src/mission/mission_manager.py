from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Tuple, List


MISSION_CREATED = "CREATED"
MISSION_ACTIVE = "ACTIVE"
MISSION_COMPLETED = "COMPLETED"
MISSION_CANCELLED = "CANCELLED"


@dataclass
class Mission:
    mission_id: str
    anchor: str
    location: Tuple[float, float]

    reason: str
    risk_level: str

    drone_id: Optional[str] = None

    status: str = MISSION_CREATED

    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    notes: List[str] = field(default_factory=list)


class MissionManager:
    """
    Manages ELIOS-SAR reconnaissance missions.

    This layer does not directly control the drone.
    It manages mission state and mission information.
    """

    def __init__(self):
        self.missions = {}
        self._mission_counter = 0

    def create_mission(
        self,
        anchor: str,
        location: Tuple[float, float],
        reason: str,
        risk_level: str,
    ) -> Mission:

        self._mission_counter += 1

        mission_id = f"MISSION-{self._mission_counter:03d}"

        mission = Mission(
            mission_id=mission_id,
            anchor=anchor,
            location=location,
            reason=reason,
            risk_level=risk_level,
        )

        self.missions[mission_id] = mission

        return mission

    def assign_drone(
        self,
        mission_id: str,
        drone_id: str,
    ) -> bool:

        mission = self.get_mission(mission_id)

        if mission is None:
            return False

        if mission.status != MISSION_CREATED:
            return False

        mission.drone_id = drone_id

        return True

    def start_mission(
        self,
        mission_id: str,
    ) -> bool:

        mission = self.get_mission(mission_id)

        if mission is None:
            return False

        if mission.status != MISSION_CREATED:
            return False

        if mission.drone_id is None:
            return False

        mission.status = MISSION_ACTIVE
        mission.started_at = datetime.now()

        return True

    def complete_mission(
        self,
        mission_id: str,
    ) -> bool:

        mission = self.get_mission(mission_id)

        if mission is None:
            return False

        if mission.status != MISSION_ACTIVE:
            return False

        mission.status = MISSION_COMPLETED
        mission.completed_at = datetime.now()

        return True

    def cancel_mission(
        self,
        mission_id: str,
    ) -> bool:

        mission = self.get_mission(mission_id)

        if mission is None:
            return False

        if mission.status == MISSION_COMPLETED:
            return False

        mission.status = MISSION_CANCELLED
        mission.completed_at = datetime.now()

        return True

    def add_note(
        self,
        mission_id: str,
        note: str,
    ) -> bool:

        mission = self.get_mission(mission_id)

        if mission is None:
            return False

        mission.notes.append(note)

        return True

    def get_mission(
        self,
        mission_id: str,
    ) -> Optional[Mission]:

        return self.missions.get(mission_id)

    def get_active_missions(self) -> List[Mission]:

        return [
            mission
            for mission in self.missions.values()
            if mission.status == MISSION_ACTIVE
        ]

    def get_all_missions(self) -> List[Mission]:

        return list(self.missions.values())
