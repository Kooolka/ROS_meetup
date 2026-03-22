import rclpy                                                                                                   
from rclpy.node import Node                                                                                    
from geometry_msgs.msg import Twist                                                                            
import serial                                                                                                  
import struct                                                                                                  
import time                                                                                                    
                                                                                                               
class SerialBridge(Node):                                                                                      
    def __init__(self):                                                                                        
        super().__init__('serial_bridge')                                                                      
        self.declare_parameter('port', '/dev/ttyUSB0')                                                         
        self.declare_parameter('baudrate', 115200)                                                             
        self.declare_parameter('reconnect_interval', 2.0)                                                      
                                                                                                               
        self.port = self.get_parameter('port').value                                                           
        self.baud = self.get_parameter('baudrate').value                                                       
        self.reconnect_interval = self.get_parameter('reconnect_interval').value                               
                                                                                                               
        self.ser = None                                                                                        
        self.connect_serial()                                                                                  
                                                                                                               
        self.subscription = self.create_subscription(                                                          
            Twist,                                                                                             
            '/cmd_vel',                                                                                        
            self.cmd_vel_callback,                                                                             
            10)                                                                                                
                                                                                                               
        # Timer for periodic connection check                                                                  
        self.timer = self.create_timer(5.0, self.check_connection)                                             
                                                                                                               
    def connect_serial(self):                                                                                  
        if self.ser is not None:                                                                               
            try:                                                                                               
                self.ser.close()                                                                               
            except:                                                                                            
                pass                                                                                           
            self.ser = None                                                                                    
                                                                                                               
        try:                                                                                                   
            self.ser = serial.Serial(self.port, self.baud, timeout=1)                                          
            self.get_logger().info(f'Connected to {self.port} at {self.baud} baud')                            
            return True                                                                                        
        except serial.SerialException as e:                                                                    
            self.get_logger().error(f'Failed to open serial port: {e}')                                        
            self.ser = None                                                                                    
            return False                                                                                       
                                                                                                               
    def check_connection(self):                                                                                
        if self.ser is None:                                                                                   
            self.get_logger().warn('Attempting to reconnect to serial port...')                                
            self.connect_serial()                                                                              
        else:                                                                                                  
            # Try to write a dummy byte to check if connection is alive                                        
            try:                                                                                               
                self.ser.write(b'')                                                                            
            except:                                                                                            
                self.get_logger().warn('Serial connection lost. Reconnecting...')                              
                self.ser = None                                                                                
                self.connect_serial()                                                                          
                                                                                                               
    def cmd_vel_callback(self, msg):                                                                           
        if self.ser is None:                                                                                   
            # Try to reconnect immediately                                                                     
            if not self.connect_serial():                                                                      
                return                                                                                         
                                                                                                               
        try:                                                                                                   
            # Pack linear x, angular z into two floats                                                         
            data = struct.pack('<ff', msg.linear.x, msg.angular.z)                                             
            self.ser.write(data)                                                                               
            self.get_logger().debug(f'Sent linear: {msg.linear.x:.2f}, angular: {msg.angular.z:.2f}')          
        except Exception as e:                                                                                 
            self.get_logger().error(f'Failed to send data: {e}')                                               
            self.ser = None                                                                                    
                                                                                                               
def main(args=None):                                                                                           
    rclpy.init(args=args)                                                                                      
    node = SerialBridge()                                                                                      
    rclpy.spin(node)                                                                                           
    node.destroy_node()                                                                                        
    rclpy.shutdown()                                                                                           
                                                                                                               
if __name__ == '__main__':                                                                                     
    main()                     