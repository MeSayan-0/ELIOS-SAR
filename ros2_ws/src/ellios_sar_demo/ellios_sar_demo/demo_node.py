#!/usr/bin/env python3
import json, math, time
from typing import List, Tuple

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import PoseStamped, Quaternion
from sensor_msgs.msg import LaserScan
from nav_msgs.msg import OccupancyGrid, MapMetaData


def yaw_to_quat(yaw: float) -> Quaternion:
    q = Quaternion()
    q.z = math.sin(yaw / 2.0)
    q.w = math.cos(yaw / 2.0)
    return q


class ElliosDemoNode(Node):
    """Hardware-shaped ROS2 simulator for validating the GCS without Gazebo.

    It publishes the same topic contracts that the final GCS expects.
    Replace this node with Gazebo + real sensor drivers later; the browser
    does not need to change.
    """
    def __init__(self):
        super().__init__('ellios_sar_demo')
        self.t0 = time.monotonic()
        self.pub_rover_pose = self.create_publisher(PoseStamped, '/rover/pose', 10)
        self.pub_drone_pose = self.create_publisher(PoseStamped, '/drone/pose', 10)
        self.pub_rover_scan = self.create_publisher(LaserScan, '/rover/scan', 10)
        self.pub_drone_scan = self.create_publisher(LaserScan, '/drone/scan', 10)
        self.pub_map = self.create_publisher(OccupancyGrid, '/map', 1)
        self.pub_rover_tel = self.create_publisher(String, '/rover/telemetry', 10)
        self.pub_drone_tel = self.create_publisher(String, '/drone/telemetry', 10)
        self.pub_env = self.create_publisher(String, '/rover/environment', 10)
        self.pub_events = self.create_publisher(String, '/system/events', 10)
        self.map_msg = self.make_map()
        self.last_event = 0.0
        self.create_timer(0.1, self.tick)
        self.create_timer(2.0, self.publish_map)
        self.get_logger().info('ELLIOS-SAR ROS demo started. No hardware required.')

    def make_map(self) -> OccupancyGrid:
        # 40m x 24m at 0.1m resolution. Simple mine galleries with walls.
        w, h, res = 400, 240, 0.1
        data = [0] * (w*h)

        def wall(x0, y0, x1, y1):
            # coordinates in metres; make a thick wall line
            steps = max(abs(x1-x0), abs(y1-y0), 1) * 20
            for i in range(int(steps)+1):
                u = i / max(steps, 1)
                x = x0 + (x1-x0)*u
                y = y0 + (y1-y0)*u
                cx, cy = int(x/res), int(y/res)
                for dx in range(-2, 3):
                    for dy in range(-2, 3):
                        xx, yy = cx+dx, cy+dy
                        if 0 <= xx < w and 0 <= yy < h:
                            data[yy*w+xx] = 100

        # Outer boundary
        wall(0,0,40,0); wall(0,24,40,24); wall(0,0,0,24); wall(40,0,40,24)
        # Galleries / rooms
        wall(4,4,34,4); wall(4,20,34,20)
        wall(4,4,4,20); wall(34,4,34,20)
        wall(4,12,14,12); wall(20,12,34,12)
        wall(14,4,14,9); wall(14,15,14,20)
        wall(20,4,20,9); wall(20,15,20,20)
        wall(27,12,27,17)
        # Leave intentional doorway gaps by clearing a few areas.
        for gx, gy in [(14,12),(20,12),(14,9),(20,9),(27,12)]:
            cx,cy=int(gx/res),int(gy/res)
            for dx in range(-6,7):
                for dy in range(-6,7):
                    xx,yy=cx+dx,cy+dy
                    if 0<=xx<w and 0<=yy<h:
                        data[yy*w+xx]=0

        msg = OccupancyGrid()
        msg.header.frame_id='map'
        msg.info = MapMetaData()
        msg.info.resolution=res; msg.info.width=w; msg.info.height=h
        msg.info.origin.position.x=0.0; msg.info.origin.position.y=0.0
        msg.data=data
        return msg

    def rover_state(self, t):
        # Smooth loop inside the galleries.
        x = 8.0 + 12.0 * (0.5 + 0.5*math.sin(t/9.0))
        y = 12.0 + 4.0 * math.sin(t/9.0)
        yaw = math.atan2(4.0*math.cos(t/9.0), (12.0/9.0)*0.5*math.cos(t/9.0))
        return x,y,yaw

    def drone_state(self, t):
        x = 16.0 + 5.0*math.sin(t/6.0)
        y = 12.0 + 3.0*math.cos(t/6.0)
        z = 4.0 + 0.6*math.sin(t/4.0)
        yaw = (t/8.0) % (2*math.pi)
        return x,y,z,yaw

    def make_scan(self, x, y, yaw, drone=False):
        # Ray-cast against the rectangular mine walls, 360 rays.
        n=360; amin=-math.pi; inc=2*math.pi/n
        ranges=[]
        maxr=15.0 if not drone else 10.0
        for i in range(n):
            a=yaw+amin+i*inc
            r=maxr
            # Outer rectangle intersections
            ca,sa=math.cos(a),math.sin(a)
            candidates=[]
            if abs(ca)>1e-6:
                for wx in (0,40):
                    rr=(wx-x)/ca
                    if rr>0: candidates.append(rr)
            if abs(sa)>1e-6:
                for wy in (0,24):
                    rr=(wy-y)/sa
                    if rr>0: candidates.append(rr)
            # gallery walls (selected line segments)
            segs=[(4,4,34,4),(4,20,34,20),(4,12,14,12),(20,12,34,12),
                  (4,4,4,20),(34,4,34,20),(14,4,14,9),(14,15,14,20),
                  (20,4,20,9),(20,15,20,20),(27,12,27,17)]
            for x1,y1,x2,y2 in segs:
                den=(-sa*(x2-x1)+ca*(y2-y1))
                if abs(den)<1e-8: continue
                rr=(-sa*(x1-x)+ca*(y1-y))/den
                u=(ca*(y1-y)-sa*(x1-x))/den
                if rr>0 and 0<=u<=1: candidates.append(rr)
            positives=[v for v in candidates if v>0]
            if positives: r=min(r,min(positives))
            ranges.append(float(max(0.08,min(maxr,r))))
        return ranges, amin, inc

    def pose_msg(self, frame, x,y,z,yaw):
        m=PoseStamped(); m.header.frame_id=frame; m.header.stamp=self.get_clock().now().to_msg()
        m.pose.position.x=x; m.pose.position.y=y; m.pose.position.z=z
        m.pose.orientation=yaw_to_quat(yaw)
        return m

    def scan_msg(self, frame, ranges, amin, inc):
        m=LaserScan(); m.header.frame_id=frame; m.header.stamp=self.get_clock().now().to_msg()
        m.angle_min=amin; m.angle_max=amin+len(ranges)*inc; m.angle_increment=inc
        m.range_min=0.08; m.range_max=15.0; m.ranges=ranges
        return m

    def tick(self):
        t=time.monotonic()-self.t0
        rx,ry,ryaw=self.rover_state(t)
        dx,dy,dz,dyaw=self.drone_state(t)

        self.pub_rover_pose.publish(self.pose_msg('map',rx,ry,0.0,ryaw))
        self.pub_drone_pose.publish(self.pose_msg('map',dx,dy,dz,dyaw))

        rr,amin,inc=self.make_scan(rx,ry,ryaw)
        dr,_,_=self.make_scan(dx,dy,dyaw,True)
        self.pub_rover_scan.publish(self.scan_msg('rover_lidar',rr,amin,inc))
        self.pub_drone_scan.publish(self.scan_msg('drone_lidar',dr,amin,inc))

        rover_bat=max(35.0, 82.0-0.02*t)
        drone_bat=max(25.0, 76.0-0.05*t)
        self.pub_rover_tel.publish(String(data=json.dumps({
            'battery':round(rover_bat,1),'speed':round(0.65+0.15*math.sin(t/3),2),
            'heading':round((math.degrees(ryaw)%360),1),'slam':'LOCKED','lidar_rate':3600
        })))
        self.pub_drone_tel.publish(String(data=json.dumps({
            'battery':round(drone_bat,1),'altitude':round(dz,2),
            'yaw':round(math.degrees(dyaw)%360,1),'mode':'SURVEY','link':-58
        })))
        methane=0.65+0.25*math.sin(t/5.0)
        self.pub_env.publish(String(data=json.dumps({
            'methane':round(methane,2),'ch4':round(methane,2),
            'co':round(18+4*math.sin(t/7.0),1),'oxygen':20.7,
            'temperature':29.1+0.8*math.sin(t/11.0),'humidity':79+3*math.sin(t/13.0)
        })))
        if t-self.last_event>12:
            self.pub_events.publish(String(data='Rover scan updated • local frontier refreshed'))
            self.last_event=t

    def publish_map(self):
        self.map_msg.header.stamp=self.get_clock().now().to_msg()
        self.pub_map.publish(self.map_msg)


def main(args=None):
    rclpy.init(args=args)
    node=ElliosDemoNode()
    try: rclpy.spin(node)
    except KeyboardInterrupt: pass
    finally:
        node.destroy_node(); rclpy.shutdown()


if __name__ == '__main__':
    main()
