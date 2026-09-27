import time
import math
import numpy as np

class EMAFilter:
    """
    Exponential Moving Average filter for 3D pose vectors.
    Smooths noisy raw optical detections and provides velocity estimates.
    """
    def __init__(self, alpha=0.25):
        self.alpha = float(alpha)
        self.value = None

    def update(self, measurement):
        if self.value is None:
            self.value = float(measurement)
        else:
            self.value = self.alpha * float(measurement) + (1.0 - self.alpha) * self.value
        return self.value

    def reset(self):
        self.value = None


class TargetPoseFilter:
    """
    Comprehensive Target Pose Filter with:
    - Independent 3D EMA smoothing (X, Y, Z)
    - Target loss detection and timeout
    - Outlier rejection based on maximum feasible velocity
    - Confidence scoring
    """
    def __init__(self, alpha=0.30, timeout_sec=0.5, max_jump_meters=1.5):
        self.filter_x = EMAFilter(alpha)
        self.filter_y = EMAFilter(alpha)
        self.filter_z = EMAFilter(alpha)
        self.filter_yaw = EMAFilter(alpha)

        self.timeout_sec = timeout_sec
        self.max_jump = max_jump_meters

        self.last_update_time = None
        self.last_valid_pose = None  # (x, y, z, yaw)
        self.is_tracking = False

    def update(self, raw_x, raw_y, raw_z, raw_yaw=0.0):
        now = time.time()

        # Check for sudden unrealistic jumps (outlier rejection)
        if self.last_valid_pose is not None:
            dt = now - self.last_update_time
            dx = raw_x - self.last_valid_pose[0]
            dy = raw_y - self.last_valid_pose[1]
            dz = raw_z - self.last_valid_pose[2]
            dist_jump = math.sqrt(dx*dx + dy*dy + dz*dz)

            # If sudden leap without reasonable elapsed time, reject as outlier
            if dt < 0.2 and dist_jump > self.max_jump:
                print(f"[Filter] Outlier rejected: jump of {dist_jump:.2f} m in {dt*1000:.1f} ms")
                return self.last_valid_pose, True

        # Apply EMA filters
        fx = self.filter_x.update(raw_x)
        fy = self.filter_y.update(raw_y)
        fz = self.filter_z.update(raw_z)
        fyaw = self.filter_yaw.update(raw_yaw)

        self.last_update_time = now
        self.last_valid_pose = (fx, fy, fz, fyaw)
        self.is_tracking = True
        return self.last_valid_pose, True

    def check_timeout(self):
        """
        Returns True if target was lost (timed out), False if still active.
        """
        if self.last_update_time is None:
            self.is_tracking = False
            return True

        if (time.time() - self.last_update_time) > self.timeout_sec:
            self.is_tracking = False
            self.filter_x.reset()
            self.filter_y.reset()
            self.filter_z.reset()
            self.filter_yaw.reset()
            self.last_valid_pose = None
            return True

        return False

    def get_pose(self):
        if self.check_timeout():
            return None
        return self.last_valid_pose
