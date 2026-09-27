#!/usr/bin/env python3

import math

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
from geometry_msgs.msg import TransformStamped
from sensor_msgs.msg import PointCloud2
from px4_msgs.msg import VehicleLocalPosition
from px4_msgs.msg import VehicleAttitude

from tf2_ros import TransformBroadcaster, StaticTransformBroadcaster


class V3PoseTFAdapter(Node):

    def __init__(self):
        super().__init__('v3_pose_tf_adapter')

        self.position = None
        self.attitude = None
        px4_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
            depth=10
        )

        self.tf_broadcaster = TransformBroadcaster(self)
        self.static_tf_broadcaster = StaticTransformBroadcaster(self)

        self.position_sub = self.create_subscription(
            VehicleLocalPosition,
            '/fmu/out/vehicle_local_position_v1',
            self.position_callback,
            px4_qos
        )

        self.attitude_sub = self.create_subscription(
            VehicleAttitude,
            '/fmu/out/vehicle_attitude',
            self.attitude_callback,
            px4_qos
        )

        self.lidar_sub = self.create_subscription(
            PointCloud2,
            '/drone/lidar/points/points',
            self.lidar_callback,
            10
        )

        self.lidar_pub = self.create_publisher(
            PointCloud2,
            '/drone_v3/lidar/points',
            10
        )

        self.timer = self.create_timer(
            0.02,
            self.publish_drone_tf
        )

        self.publish_static_lidar_tf()

        self.get_logger().info(
            'ELIOS-SAR V3 Pose/TF Adapter started'
        )

    def position_callback(self, msg):
        self.position = msg

    def attitude_callback(self, msg):
        self.attitude = msg

    def publish_static_lidar_tf(self):

        transform = TransformStamped()

        transform.header.stamp = self.get_clock().now().to_msg()

        transform.header.frame_id = 'drone_v3/base_link'
        transform.child_frame_id = 'drone_v3/lidar_link'

        transform.transform.translation.x = 0.0
        transform.transform.translation.y = 0.0
        transform.transform.translation.z = -0.035

        transform.transform.rotation.x = 0.0
        transform.transform.rotation.y = 0.0
        transform.transform.rotation.z = 0.0
        transform.transform.rotation.w = 1.0

        self.static_tf_broadcaster.sendTransform(transform)

    def publish_drone_tf(self):

        if self.position is None:
            return

        if self.attitude is None:
            return

        msg = self.position

        transform = TransformStamped()

        transform.header.stamp = self.get_clock().now().to_msg()

        transform.header.frame_id = 'map'
        transform.child_frame_id = 'drone_v3/base_link'

        # PX4 NED → ROS ENU
        #
        # PX4:
        #   x = North
        #   y = East
        #   z = Down
        #
        # ROS:
        #   X = East
        #   Y = North
        #   Z = Up

        transform.transform.translation.x = float(msg.y)
        transform.transform.translation.y = float(msg.x)
        transform.transform.translation.z = float(-msg.z)

        q = self.attitude.q

        # PX4 attitude quaternion
        q0 = float(q[0])
        q1 = float(q[1])
        q2 = float(q[2])
        q3 = float(q[3])

        # PX4 quaternion → ROS ENU orientation
        transform.transform.rotation.x = -q2
        transform.transform.rotation.y = -q1
        transform.transform.rotation.z = q3
        transform.transform.rotation.w = q0

        self.tf_broadcaster.sendTransform(transform)

    def lidar_callback(self, msg):

        cloud = PointCloud2()

        cloud.header = msg.header

        cloud.header.frame_id = 'drone_v3/lidar_link'

        cloud.height = msg.height
        cloud.width = msg.width

        cloud.fields = msg.fields
        cloud.is_bigendian = msg.is_bigendian

        cloud.point_step = msg.point_step
        cloud.row_step = msg.row_step

        cloud.data = msg.data

        cloud.is_dense = msg.is_dense

        self.lidar_pub.publish(cloud)


def main(args=None):

    rclpy.init(args=args)

    node = V3PoseTFAdapter()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
