import rclpy
from rclpy.node import Node
from rclpy.qos import (
    QoSProfile,
    ReliabilityPolicy,
    DurabilityPolicy,
    HistoryPolicy,
)

from px4_msgs.msg import OffboardControlMode
from px4_msgs.msg import TrajectorySetpoint


class ElliosSAROffboardController(Node):

    def __init__(self):
        super().__init__('ellios_sar_px4_offboard')

        # PX4 uXRCE QoS configuration
        self.px4_qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
        )

        self.offboard_control_mode_pub = self.create_publisher(
            OffboardControlMode,
            '/fmu/in/offboard_control_mode',
            self.px4_qos,
        )

        self.trajectory_setpoint_pub = self.create_publisher(
            TrajectorySetpoint,
            '/fmu/in/trajectory_setpoint',
            self.px4_qos,
        )

        self.timer = self.create_timer(
            0.1,
            self.publish_setpoints,
        )

        self.counter = 0

        self.get_logger().info(
            'ELIOS-SAR Offboard controller started'
        )

        self.get_logger().info(
            'Publishing OffboardControlMode + TrajectorySetpoint'
        )

    def publish_setpoints(self):

        # --------------------------------------------------
        # OFFBOARD CONTROL MODE
        # --------------------------------------------------

        offboard_msg = OffboardControlMode()

        offboard_msg.position = True
        offboard_msg.velocity = False
        offboard_msg.acceleration = False
        offboard_msg.attitude = False
        offboard_msg.body_rate = False
        offboard_msg.thrust_and_torque = False
        offboard_msg.direct_actuator = False

        offboard_msg.timestamp = int(self.get_clock().now().nanoseconds // 1000)

        self.offboard_control_mode_pub.publish(
            offboard_msg
        )

        # --------------------------------------------------
        # TRAJECTORY SETPOINT
        # PX4 uses NED coordinates.
        #
        # x = 0 m
        # y = 0 m
        # z = -2 m  -> approximately 2 m above origin
        # --------------------------------------------------

        trajectory_msg = TrajectorySetpoint()

        trajectory_msg.position[0] = 0.0
        trajectory_msg.position[1] = 0.0
        trajectory_msg.position[2] = -2.0

        trajectory_msg.yaw = 0.0

        trajectory_msg.timestamp = int(self.get_clock().now().nanoseconds // 1000)

        self.trajectory_setpoint_pub.publish(
            trajectory_msg
        )

        self.counter += 1

        if self.counter % 50 == 0:
            self.get_logger().info(
                'Offboard setpoint active: '
                'x=0.0 y=0.0 z=-2.0'
            )


def main(args=None):

    rclpy.init(args=args)

    node = ElliosSAROffboardController()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
