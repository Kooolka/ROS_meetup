#!/usr/bin/env python3
"""
WebSocket backend for web teleoperation.
Publishes Twist messages to /cmd_vel and ArmCommand to /arm_command.
"""
import asyncio
import json
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from ros2_robot_platform.msg import ArmCommand
import websockets
import logging

logging.basicConfig(level=logging.INFO)

class TeleopBackend(Node):
    def __init__(self):
        super().__init__('web_teleop_backend')
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.arm_cmd_pub = self.create_publisher(ArmCommand, '/arm_command', 10)
        self.get_logger().info('Web teleop backend started')

    def publish_twist(self, linear, angular):
        msg = Twist()
        msg.linear.x = linear
        msg.angular.z = angular
        self.cmd_vel_pub.publish(msg)

    def publish_arm(self, lift, grip):
        msg = ArmCommand()
        msg.lift_speed = lift
        msg.grip_angle = grip
        self.arm_cmd_pub.publish(msg)

async def handler(websocket, path, node):
    async for message in websocket:
        try:
            data = json.loads(message)
            cmd_type = data.get('type', 'drive')
            if cmd_type == 'drive':
                linear = float(data.get('linear', 0.0))
                angular = float(data.get('angular', 0.0))
                node.publish_twist(linear, angular)
            elif cmd_type == 'arm':
                lift = float(data.get('lift', 0.0))
                grip = float(data.get('grip', 90.0))
                node.publish_arm(lift, grip)
        except Exception as e:
            logging.error(f'Error processing message: {e}')

import threading

def spin_node(node):
    rclpy.spin(node)

async def main():
    rclpy.init()
    node = TeleopBackend()
    
    # Start ROS node in a separate thread
    spin_thread = threading.Thread(target=spin_node, args=(node,), daemon=True)
    spin_thread.start()
    
    server = await websockets.serve(
        lambda ws, path: handler(ws, path, node),
        '0.0.0.0',
        8765
    )
    logging.info('WebSocket server started on port 8765')
    try:
        await server.wait_closed()
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    asyncio.run(main())
