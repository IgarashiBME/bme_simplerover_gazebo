#!/usr/bin/env python3
"""Keyboard teleop node: publishes cmd_vel based on key input."""

import atexit
import sys
import select
import termios
import tty

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

USAGE = """
Keyboard Teleop
---------------
  q : forward + turn left
  w : forward
  e : forward + turn right
  a : turn left
  d : turn right
  s : backward

  Ctrl+C : quit
"""

# key -> (linear.x [m/s], angular.z [rad/s])
KEY_MAP = {
    'w': (0.4, 0.0),
    's': (-0.4, 0.0),
    'a': (0.0, 0.4),
    'd': (0.0, -0.4),
    'q': (0.4, 0.2),
    'e': (0.4, -0.2),
}


class TeleopKeyNode(Node):
    def __init__(self):
        super().__init__('teleop_key_node')

        self.pub = self.create_publisher(Twist, 'cmd_vel', 10)
        self.timer = self.create_timer(0.1, self.timer_cb)  # 10 Hz

        # Save and switch terminal to raw mode
        self.old_settings = termios.tcgetattr(sys.stdin)
        atexit.register(termios.tcsetattr, sys.stdin, termios.TCSANOW, self.old_settings)
        tty.setcbreak(sys.stdin.fileno())

        self.get_logger().info(USAGE)

    def timer_cb(self):
        twist = Twist()

        # Drain stdin buffer and keep only the last key
        key = None
        while select.select([sys.stdin], [], [], 0.0)[0]:
            key = sys.stdin.read(1)

        if key is not None and key in KEY_MAP:
            lin_val, ang_val = KEY_MAP[key]
            twist.linear.x = lin_val
            twist.angular.z = ang_val

        self.pub.publish(twist)

    def destroy_node(self):
        # Restore terminal settings
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = TeleopKeyNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        # Send zero velocity before shutting down
        node.pub.publish(Twist())
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
