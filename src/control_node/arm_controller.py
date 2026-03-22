#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from ros2_robot_platform.msg import ArmCommand
import serial
import struct

class ArmController(Node):
    def __init__(self):
        super().__init__('arm_controller')
        self.declare_parameter('port', '/dev/ttyUSB0')
        self.declare_parameter('baudrate', 115200)
        
        port = self.get_parameter('port').value
        baud = self.get_parameter('baudrate').value
        
        try:
            self.ser = serial.Serial(port, baud, timeout=1)
            self.get_logger().info(f'Connected to {port} at {baud} baud')
        except serial.SerialException as e:
            self.get_logger().error(f'Failed to open serial port: {e}')
            self.ser = None
            
        self.subscription = self.create_subscription(
            ArmCommand,
            '/arm_command',
            self.arm_callback,
            10)
        
    def arm_callback(self, msg):
        if self.ser is None:
            return
        # Clamp values
        lift = max(-1.0, min(1.0, msg.lift_speed))
        grip = max(0.0, min(180.0, msg.grip_angle))
        # Pack two floats: lift speed, grip angle
        data = struct.pack('<ff', lift, grip)
        # Send header 'ARM2' to indicate two‑float arm command
        header = b'ARM2'
        self.ser.write(header + data)
        self.get_logger().debug(f'Sent arm: lift={lift:.2f}, grip={grip:.1f}')

def main(args=None):
    rclpy.init(args=args)
    node = ArmController()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
