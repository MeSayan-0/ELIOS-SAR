import math
import numpy as np

class CoordinateTransformer:
    """
    Transforms 3D target coordinates across reference frames:
    1. Camera Optical Frame (X: right, Y: down, Z: forward along optical axis)
    2. Drone Body Frame (FRD: X forward, Y right, Z down)
    3. Navigation Frame (NED: X North, Y East, Z Down)
    """

    def __init__(self, camera_mount="downward_standard"):
        """
        camera_mount:
        - 'downward_standard': Lens pointing down, top of camera facing vehicle front.
          X_body = -Y_cam (Forward)
          Y_body = +X_cam (Right)
          Z_body = +Z_cam (Down)
        """
        self.camera_mount = camera_mount

    def camera_to_body_frd(self, x_cam, y_cam, z_cam):
        """
        Converts camera optical coordinates (x_cam, y_cam, z_cam)
        to vehicle body frame FRD (x_body, y_body, z_body).
        """
        if self.camera_mount == "downward_standard":
            x_body = -float(y_cam)   # Camera down is vehicle backward -> -Y_cam is vehicle forward
            y_body = float(x_cam)    # Camera right is vehicle right -> +X_cam is vehicle right
            z_body = float(z_cam)    # Camera forward is pointing down -> +Z_cam is vehicle down
        else:
            # Fallback identity if camera matches body
            x_body = float(x_cam)
            y_body = float(y_cam)
            z_body = float(z_cam)

        return x_body, y_body, z_body

    def body_frd_to_local_ned(self, x_body, y_body, z_body, vehicle_yaw_rad=0.0):
        """
        Rotates body-relative target vector (FRD) by vehicle yaw heading into local NED.
        vehicle_yaw_rad: Pixhawk yaw heading in radians (0 = North, +pi/2 = East).
        """
        cos_yaw = math.cos(vehicle_yaw_rad)
        sin_yaw = math.sin(vehicle_yaw_rad)

        # 2D horizontal rotation around Down axis (Z remains invariant under pure yaw)
        x_ned = cos_yaw * x_body - sin_yaw * y_body
        y_ned = sin_yaw * x_body + cos_yaw * y_body
        z_ned = z_body

        return x_ned, y_ned, z_ned

    def compute_angles_and_distance(self, x, y, z):
        """
        Calculates angular offsets (angle_x, angle_y) and Euclidean distance
        as defined by MAVLink LANDING_TARGET protocol:
        - angle_x: target angular offset in radians along X axis (atan2(x, z))
        - angle_y: target angular offset in radians along Y axis (atan2(y, z))
        - distance: 3D Euclidean distance in meters
        """
        distance = math.sqrt(x*x + y*y + z*z)
        if z <= 0.001:
            angle_x = 0.0
            angle_y = 0.0
        else:
            angle_x = math.atan2(x, z)
            angle_y = math.atan2(y, z)

        return angle_x, angle_y, distance
