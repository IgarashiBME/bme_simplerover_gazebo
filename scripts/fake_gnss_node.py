#!/usr/bin/env python3
"""Publish Gazebo world position as GnssSolution (UTM coordinates)."""

import math

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from bme_common_msgs.msg import GnssSolution


def quaternion_to_yaw(q):
    """Extract yaw angle (rad) from quaternion."""
    siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
    cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
    return math.atan2(siny_cosp, cosy_cosp)


class FakeGnssNode(Node):
    def __init__(self):
        super().__init__('fake_gnss_node')

        # UTM origin parameters (Gazebo (0,0) corresponds to this UTM coordinate)
        self.declare_parameter('origin_latitude', 35.0)
        self.declare_parameter('origin_longitude', 139.0)
        self.declare_parameter('origin_utm_easting', 500000.0)
        self.declare_parameter('origin_utm_northing', 3873000.0)
        self.declare_parameter('origin_height', 0.0)

        self.origin_lat = self.get_parameter('origin_latitude').value
        self.origin_lon = self.get_parameter('origin_longitude').value
        self.origin_easting = self.get_parameter('origin_utm_easting').value
        self.origin_northing = self.get_parameter('origin_utm_northing').value
        self.origin_height = self.get_parameter('origin_height').value

        # Meters-per-degree constants at the origin latitude
        self.m_per_deg_lat = 111320.0
        self.m_per_deg_lon = 111320.0 * math.cos(math.radians(self.origin_lat))

        self.pub = self.create_publisher(GnssSolution, 'gnss/solution', 10)
        self.create_subscription(Odometry, 'ground_truth/odom', self.odom_cb, 10)

        self.get_logger().info(
            f'Fake GNSS started: origin UTM=({self.origin_easting}, '
            f'{self.origin_northing}), lat/lon=({self.origin_lat}, {self.origin_lon})'
        )

    def odom_cb(self, msg: Odometry):
        pos = msg.pose.pose.position
        ori = msg.pose.pose.orientation

        out = GnssSolution()
        out.header.stamp = msg.header.stamp
        out.header.frame_id = 'gnss'

        # UTM coordinates = origin + Gazebo world offset
        out.utm_easting = self.origin_easting + pos.x
        out.utm_northing = self.origin_northing + pos.y
        out.height = self.origin_height + pos.z

        # Approximate lat/lon from meter offset
        out.latitude = self.origin_lat + (pos.y / self.m_per_deg_lat)
        out.longitude = self.origin_lon + (pos.x / self.m_per_deg_lon)

        # Heading: ENU yaw in degrees (East=0, North=90, CCW positive per REP-103)
        # Range: -180 to 180
        yaw_rad = quaternion_to_yaw(ori)
        out.heading_deg = math.degrees(yaw_rad)

        # Fixed quality indicators (no simulated error)
        out.num_sv = 12
        out.position_rtk_status = 2  # Fixed
        out.heading_rtk_status = 2   # Fixed
        out.h_acc = 0
        out.v_acc = 0

        self.pub.publish(out)


def main(args=None):
    rclpy.init(args=args)
    node = FakeGnssNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
