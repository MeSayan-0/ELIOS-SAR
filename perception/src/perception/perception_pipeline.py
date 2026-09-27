from dataclasses import asdict, is_dataclass
from typing import Any


class PerceptionPipeline:
    def __init__(
        self,
        person_detector=None,
        pose_estimator=None,
        scheduler=None,
        risk_engine=None,
        pose_interval=3
    ):
        self.person_detector = person_detector
        self.pose_estimator = pose_estimator
        self.scheduler = scheduler
        self.risk_engine = risk_engine

        self.pose_interval = max(1, pose_interval)
        self.frame_counter = 0

    def process(self, frame, gas_state=None):
        frame_index = self.frame_counter
        self.frame_counter += 1

        persons = []
        if self.person_detector is not None:
            persons = self.person_detector.detect(frame)

        poses = []

        if (
            self.pose_estimator is not None and
            persons and
            frame_index % self.pose_interval == 0
        ):
            poses = self.pose_estimator.estimate(frame)

        hazards = {
            "fire": [],
            "flood": [],
            "boulder": []
        }

        if self.scheduler is not None:
            hazards = self.scheduler.run(frame)

        risk = None

        if self.risk_engine is not None:
            risk = self.risk_engine.evaluate(
                persons=persons,
                poses=poses,
                hazards=hazards,
                gas_state=gas_state
            )

        return {
            "frame_index": frame_index,
            "persons": persons,
            "poses": poses,
            "hazards": hazards,
            "risk": risk
        }

    @staticmethod
    def serialize(value: Any):
        if is_dataclass(value):
            return asdict(value)

        if isinstance(value, list):
            return [
                PerceptionPipeline.serialize(item)
                for item in value
            ]

        if isinstance(value, dict):
            return {
                key: PerceptionPipeline.serialize(item)
                for key, item in value.items()
            }

        return value

    def process_serializable(self, frame, gas_state=None):
        result = self.process(frame, gas_state)
        return self.serialize(result)
