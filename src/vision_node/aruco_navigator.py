#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseArray, Twist
import math

class ArucoNavigator(Node):
    def __init__(self):
        super().__init__('aruco_navigator')
        self.declare_parameter('target_id', 0)          # ID маркера, к которому ехать
        self.declare_parameter('target_distance', 0.3)  # Желаемая дистанция до маркера (м)
        self.declare_parameter('kp_linear', 0.5)
        self.declare_parameter('kp_angular', 1.0)
        self.declare_parameter('max_linear', 0.5)
        self.declare_parameter('max_angular', 1.0)
        
        self.subscription = self.create_subscription(
            PoseArray,
            '/detected_arucos',
            self.aruco_callback,
            10)
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        
    def aruco_callback(self, msg):
        if not msg.poses:
            self.get_logger().debug('No ArUco markers detected')
            return
        
        target_id = self.get_parameter('target_id').value
        target_distance = self.get_parameter('target_distance').value
        
        # В текущей реализации PoseArray не содержит ID, поэтому берём первый маркер
        # В реальности нужно использовать сообщение с ID, но для упрощения оставим так
        pose = msg.poses[0]
        x = pose.position.x
        y = pose.position.y
        
        # Расстояние до маркера
        distance = math.sqrt(x**2 + y**2)
        
        # Если уже достаточно близко, остановиться
        if distance < target_distance:
            cmd = Twist()
            cmd.linear.x = 0.0
            cmd.angular.z = 0.0
            self.cmd_pub.publish(cmd)
            self.get_logger().info(f'Target reached, distance: {distance:.2f}m')
            return
        
        # Угол до маркера
        angle_to_marker = math.atan2(y, x)
        
        # Пропорциональный регулятор
        kp_linear = self.get_parameter('kp_linear').value
        kp_angular = self.get_parameter('kp_angular').value
        max_linear = self.get_parameter('max_linear').value
        max_angular = self.get_parameter('max_angular').value
        
        # Линейная скорость пропорциональна расстоянию, но не более max_linear
        linear_vel = kp_linear * (distance - target_distance)
        linear_vel = max(min(linear_vel, max_linear), -max_linear)
        
        # Угловая скорость пропорциональна углу ошибки
        angular_vel = kp_angular * angle_to_marker
        angular_vel = max(min(angular_vel, max_angular), -max_angular)
        
        cmd = Twist()
        cmd.linear.x = linear_vel
        cmd.angular.z = angular_vel
        
        self.cmd_pub.publish(cmd)
        self.get_logger().debug(f'Target distance: {distance:.2f}m, linear: {linear_vel:.2f}, angular: {angular_vel:.2f}')

def main(args=None):
    rclpy.init(args=args)
    node = ArucoNavigator()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
