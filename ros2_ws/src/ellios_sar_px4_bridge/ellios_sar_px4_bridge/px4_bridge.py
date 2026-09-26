"""
ELLIOS-SAR GCS -> PX4 command bridge.

Browser:
    /gcs/drone/command
          |
          v
    this ROS 2 node
          |
          v
    /fmu/in/vehicle_command
          |
          v
         PX4

This bridge is intended for PX4 SITL first.
Keep the physical RC transmitter available when moving beyond simulation.
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import (
    QoSProfile,
    ReliabilityPolicy,
    DurabilityPolicy,
    HistoryPolicy,
)

from std_msgs.msg import String
from px4_msgs.msg import VehicleCommand, VehicleCommandAck


# MAVLink / PX4 command IDs
CMD_ARM_DISARM = 400
CMD_NAV_LOITER_UNLIM = 17
CMD_NAV_RETURN_TO_LAUNCH = 20
CMD_NAV_LAND = 21
CMD_NAV_TAKEOFF = 22
CMD_DO_SET_MODE = 176


class Px4Bridge(Node):

    def __init__(self):
        super().__init__("ellios_sar_px4_bridge")

        # ------------------------------------------------------------
        # Parameters
        # ------------------------------------------------------------

        self.declare_parameter(
            "command_topic",
            "/gcs/drone/command",
        )

        self.declare_parameter(
            "ack_topic",
            "/fmu/out/vehicle_command_ack_v1",
        )

        self.declare_parameter(
            "target_system",
            1,
        )

        self.declare_parameter(
            "target_component",
            1,
        )

        self.declare_parameter(
            "source_system",
            255,
        )

        self.declare_parameter(
            "source_component",
            1,
        )

        self.declare_parameter(
            "takeoff_altitude",
            2.0,
        )

        command_topic = self.get_parameter(
            "command_topic"
        ).value

        ack_topic = self.get_parameter(
            "ack_topic"
        ).value

        # ------------------------------------------------------------
        # PX4 QoS
        #
        # PX4 uXRCE-DDS uses:
        #   reliability = BEST_EFFORT
        #   durability  = TRANSIENT_LOCAL for publications
        #   history     = KEEP_LAST
        #
        # This avoids the RELIABILITY QoS mismatch seen previously.
        # ------------------------------------------------------------

        self.px4_pub_qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
        )

        self.px4_sub_qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
        )

        # ------------------------------------------------------------
        # Publishers
        # ------------------------------------------------------------

        self.command_pub = self.create_publisher(
            VehicleCommand,
            "/fmu/in/vehicle_command",
            self.px4_pub_qos,
        )

        self.status_pub = self.create_publisher(
            String,
            "/gcs/drone/command_status",
            10,
        )

        # ------------------------------------------------------------
        # GCS command subscriber
        # ------------------------------------------------------------

        self.command_sub = self.create_subscription(
            String,
            command_topic,
            self.command_cb,
            10,
        )

        # ------------------------------------------------------------
        # PX4 ACK subscriber
        # ------------------------------------------------------------

        self.ack_sub = self.create_subscription(
            VehicleCommandAck,
            ack_topic,
            self.ack_cb,
            self.px4_sub_qos,
        )

        self.get_logger().info(
            f"Listening for GCS commands on {command_topic}"
        )

        self.get_logger().info(
            "Publishing PX4 VehicleCommand on "
            "/fmu/in/vehicle_command"
        )

        self.get_logger().info(
            f"Listening for PX4 ACK on {ack_topic}"
        )

        self.get_logger().info(
            "PX4 QoS: BEST_EFFORT"
        )

    # ------------------------------------------------------------
    # Timestamp
    # ------------------------------------------------------------

    def stamp_us(self):
        return int(
            self.get_clock().now().nanoseconds // 1000
        )

    # ------------------------------------------------------------
    # Send VehicleCommand to PX4
    # ------------------------------------------------------------

    def send(
        self,
        command,
        p1=0.0,
        p2=0.0,
        p3=0.0,
        p7=0.0,
    ):

        msg = VehicleCommand()

        msg.timestamp = self.stamp_us()

        msg.param1 = float(p1)
        msg.param2 = float(p2)
        msg.param3 = float(p3)
        msg.param4 = 0.0
        msg.param5 = 0.0
        msg.param6 = 0.0
        msg.param7 = float(p7)

        msg.command = int(command)

        msg.target_system = int(
            self.get_parameter(
                "target_system"
            ).value
        )

        msg.target_component = int(
            self.get_parameter(
                "target_component"
            ).value
        )

        msg.source_system = int(
            self.get_parameter(
                "source_system"
            ).value
        )

        msg.source_component = int(
            self.get_parameter(
                "source_component"
            ).value
        )

        msg.confirmation = 0

        # Required for external ROS 2 control.
        msg.from_external = True

        self.command_pub.publish(msg)

    # ------------------------------------------------------------
    # Browser command callback
    # ------------------------------------------------------------

    def command_cb(self, msg: String):

        cmd = (msg.data or "").strip().upper()

        if not cmd:
            return

        self.get_logger().info(
            f"Received GCS command: {cmd}"
        )

        try:

            if cmd == "ARM":

                self.send(
                    CMD_ARM_DISARM,
                    p1=1.0,
                )

            elif cmd == "DISARM":

                self.send(
                    CMD_ARM_DISARM,
                    p1=0.0,
                )

            elif cmd == "OFFBOARD":

                self.send(
                    CMD_DO_SET_MODE,
                    p1=1.0,
                    p2=6.0,
                )

            elif cmd == "TAKEOFF":

                altitude = float(
                    self.get_parameter(
                        "takeoff_altitude"
                    ).value
                )

                self.send(
                    CMD_NAV_TAKEOFF,
                    p7=altitude,
                )

            elif cmd == "HOVER":

                self.send(
                    CMD_DO_SET_MODE,
                    p1=1.0,
                    p2=4.0,
                    p3=3.0,
                )

            elif cmd in ("LAND", "ABORT"):

                self.send(
                    CMD_NAV_LAND
                )

            elif cmd in ("RETURN_TO_DOCK", "RTL"):

                # For SITL, RTL is used as the temporary
                # return-to-dock behavior.
                self.send(
                    CMD_NAV_RETURN_TO_LAUNCH
                )

            else:

                self.publish_status(
                    f"UNKNOWN COMMAND: {cmd}"
                )

                self.get_logger().warning(
                    f"Unknown GCS command: {cmd}"
                )

                return

            self.publish_status(
                f"SENT {cmd}"
            )

            self.get_logger().info(
                f"Sent PX4 command for {cmd}"
            )

        except Exception as exc:

            self.get_logger().error(
                f"Command {cmd} failed: {exc}"
            )

            self.publish_status(
                f"ERROR {cmd}: {exc}"
            )

    # ------------------------------------------------------------
    # PX4 ACK callback
    # ------------------------------------------------------------

    def ack_cb(self, msg: VehicleCommandAck):

        text = (
            f"ACK command={msg.command} "
            f"result={msg.result} "
            f"param1={msg.result_param1} "
            f"param2={msg.result_param2}"
        )

        self.get_logger().info(text)

        self.publish_status(text)

    # ------------------------------------------------------------
    # Status publisher
    # ------------------------------------------------------------

    def publish_status(self, text):

        self.status_pub.publish(
            String(data=text)
        )


# ----------------------------------------------------------------
# Main
# ----------------------------------------------------------------

def main(args=None):

    rclpy.init(args=args)

    node = Px4Bridge()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
