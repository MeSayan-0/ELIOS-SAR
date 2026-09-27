from __future__ import annotations

from dataclasses import dataclass


@dataclass
class VIOPose:
    available: bool = False
    frame: str = "mine_local"

    x: float | None = None
    y: float | None = None
    z: float | None = None

    roll: float | None = None
    pitch: float | None = None
    yaw: float | None = None

    tracking_quality: float = 0.0


class VIOProvider:
    """
    Interface for camera + IMU visual-inertial odometry.

    Do not return fake coordinates.
    Until a real VIO backend is connected, pose is unavailable.
    """

    def __init__(self):
        self.pose = VIOPose()

    def update_from_vio(
        self,
        x: float,
        y: float,
        z: float,
        roll: float,
        pitch: float,
        yaw: float,
        tracking_quality: float,
    ):
        self.pose = VIOPose(
            available=True,
            frame="mine_local",
            x=float(x),
            y=float(y),
            z=float(z),
            roll=float(roll),
            pitch=float(pitch),
            yaw=float(yaw),
            tracking_quality=float(tracking_quality),
        )

    def get_pose(self) -> dict | None:
        if not self.pose.available:
            return None

        return {
            "frame": self.pose.frame,
            "x": self.pose.x,
            "y": self.pose.y,
            "z": self.pose.z,
            "roll": self.pose.roll,
            "pitch": self.pose.pitch,
            "yaw": self.pose.yaw,
            "tracking_quality": self.pose.tracking_quality,
        }
