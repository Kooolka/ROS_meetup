import rclpy                                                                                                   
from rclpy.node import Node                                                                                    
from geometry_msgs.msg import PoseArray, Twist                                                                 
import math                                                                                                    
                                                                                                               
class ArucoNavigator(Node):                                                                                    
    def __init__(self):                                                                                        
        super().__init__('aruco_navigator')                                                                    
        self.subscription = self.create_subscription(                                                          
            PoseArray,                                                                                         
            '/detected_arucos',                                                                                
            self.aruco_callback,                                                                               
            10)                                                                                                
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)                                            
                                                                                                               
        # Target position (x, y) in meters relative to robot                                                   
        self.target_x = 0.5                                                                                    
        self.target_y = 0.0                                                                                    
                                                                                                               
        self.kp_linear = 0.5                                                                                   
        self.kp_angular = 1.0                                                                                  
                                                                                                               
    def aruco_callback(self, msg):                                                                             
        if not msg.poses:                                                                                      
            self.get_logger().warn('No ArUco markers detected')                                                
            return                                                                                             
                                                                                                               
        # For simplicity, use the first detected marker                                                        
        pose = msg.poses[0]                                                                                    
        x = pose.position.x                                                                                    
        y = pose.position.y                                                                                    
                                                                                                               
        # Calculate error                                                                                      
        error_x = self.target_x - x                                                                            
        error_y = self.target_y - y                                                                            
                                                                                                               
        # Simple P-controller                                                                                  
        linear_vel = self.kp_linear * error_x                                                                  
        angular_vel = self.kp_angular * math.atan2(error_y, error_x)                                           
                                                                                                               
        # Limit velocities                                                                                     
        linear_vel = max(min(linear_vel, 0.5), -0.5)                                                           
        angular_vel = max(min(angular_vel, 1.0), -1.0)                                                         
                                                                                                               
        cmd = Twist()                                                                                          
        cmd.linear.x = linear_vel                                                                              
        cmd.angular.z = angular_vel                                                                            
                                                                                                               
        self.cmd_pub.publish(cmd)                                                                              
        self.get_logger().info(f'Publishing cmd_vel: linear={linear_vel:.2f}, angular={angular_vel:.2f}')      
                                                                                                               
def main(args=None):                                                                                           
    rclpy.init(args=args)                                                                                      
    node = ArucoNavigator()                                                                                    
    rclpy.spin(node)                                                                                           
    node.destroy_node()                                                                                        
    rclpy.shutdown()                                                                                           
                                                                                                               
if __name__ == '__main__':                                                                                     
    main() 
    