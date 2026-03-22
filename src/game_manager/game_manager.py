import rclpy                                                                                                   
from rclpy.node import Node                                                                                    
from std_msgs.msg import Empty, Float32                                                                        
from geometry_msgs.msg import Twist                                                                            
import time                                                                                                    
                                                                                                               
class GameManager(Node):                                                                                       
    def __init__(self):                                                                                        
        super().__init__('game_manager')                                                                       
        self.declare_parameter('match_duration', 90.0)  # seconds                                              
                                                                                                               
        self.timer_pub = self.create_publisher(Float32, '/match_time_remaining', 10)                           
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)                                        
                                                                                                               
        self.start_sub = self.create_subscription(Empty, '/match_start', self.start_callback, 10)              
        self.stop_sub = self.create_subscription(Empty, '/match_stop', self.stop_callback, 10)                 
                                                                                                               
        self.match_start_time = None                                                                           
        self.match_duration = self.get_parameter('match_duration').value                                       
        self.is_running = False                                                                                
                                                                                                               
        self.timer = self.create_timer(0.1, self.update)  # 10 Hz                                              
                                                                                                               
    def start_callback(self, msg):                                                                             
        self.get_logger().info('Match started!')                                                               
        self.match_start_time = time.time()                                                                    
        self.is_running = True                                                                                 
                                                                                                               
    def stop_callback(self, msg):                                                                              
        self.get_logger().info('Match stopped by command.')                                                    
        self.is_running = False                                                                                
        self.stop_robot()                                                                                      
                                                                                                               
    def update(self):                                                                                          
        if not self.is_running or self.match_start_time is None:                                               
            return                                                                                             
                                                                                                               
        elapsed = time.time() - self.match_start_time                                                          
        remaining = max(0.0, self.match_duration - elapsed)                                                    
                                                                                                               
        # Publish remaining time                                                                               
        time_msg = Float32()                                                                                   
        time_msg.data = remaining                                                                              
        self.timer_pub.publish(time_msg)                                                                       
                                                                                                               
        # Stop robot when time is up                                                                           
        if remaining <= 0.0:                                                                                   
            self.get_logger().info('Match time elapsed!')                                                      
            self.is_running = False                                                                            
            self.stop_robot()                                                                                  
                                                                                                               
    def stop_robot(self):                                                                                      
        cmd = Twist()                                                                                          
        cmd.linear.x = 0.0                                                                                     
        cmd.angular.z = 0.0                                                                                    
        self.cmd_vel_pub.publish(cmd)                                                                          
        self.get_logger().info('Robot stopped.')                                                               
                                                                                                               
def main(args=None):                                                                                           
    rclpy.init(args=args)                                                                                      
    node = GameManager()                                                                                       
    rclpy.spin(node)                                                                                           
    node.destroy_node()                                                                                        
    rclpy.shutdown()                                                                                           
                                                                                                               
if __name__ == '__main__':                                                                                     
    main()                         