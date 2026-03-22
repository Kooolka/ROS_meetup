#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, PoseArray
import math

class PathPlanner(Node):
    def __init__(self):
        super().__init__('path_planner')
        self.subscription = self.create_subscription(
            PoseArray,
            '/detected_arucos',
            self.aruco_callback,
            10)
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel_nav', 10)
        
        # State machine
        self.state = 'IDLE'
        self.target_id = None
        
    def aruco_callback(self, msg):
        # Simple planner: if we see marker with ID 0, move towards it
        for i, pose in enumerate(msg.poses):
            # In a real scenario, we would use marker IDs from msg.ids
            # For now, assume first marker is target
            x = pose.position.x
            y = pose.position.y
            
            # If marker is close enough, stop
            distance = math.sqrt(x**2 + y**2)
            if distance < 0.1:
                cmd = Twist()
                cmd.linear.x = 0.0
                cmd.angular.z = 0.0
                self.cmd_pub.publish(cmd)
                self.get_logger().info('Target reached')
            else:
                # Move towards marker
                cmd = Twist()
                cmd.linear.x = 0.2
                # Turn towards marker
                angle_to_marker = math.atan2(y, x)
                cmd.angular.z = 0.5 * angle_to_marker
                self.cmd_pub.publish(cmd)
                self.get_logger().info(f'Moving towards marker, distance: {distance:.2f}')
            break

def main(args=None):
    rclpy.init(args=args)
    node = PathPlanner()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
