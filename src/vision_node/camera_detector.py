import rclpy                                                                                                   
from rclpy.node import Node                                                                                    
from sensor_msgs.msg import Image                                                                              
from geometry_msgs.msg import PoseArray, Pose                                                                  
from ros2_robot_platform.msg import DetectedObject, DetectedObjectArray                                        
from cv_bridge import CvBridge                                                                                 
import cv2                                                                                                     
import numpy as np                                                                                             
import yaml                                                                                                    
import os                                                                                                      
from ament_index_python.packages import get_package_share_directory                                            
                                                                                                               
class CameraDetector(Node):                                                                                    
    def __init__(self):                                                                                        
        super().__init__('camera_detector')                                                                    
        self.declare_parameter('show_image', False)                                                            
        self.declare_parameter('use_charuco', True)                                                            
        self.declare_parameter('calibration_file', 'camera_calibration.yaml')                                  
        self.subscription = self.create_subscription(                                                          
            Image,                                                                                             
            '/camera/image_raw',                                                                               
            self.image_callback,                                                                               
            10)                                                                                                
        self.pose_pub = self.create_publisher(PoseArray, '/detected_arucos', 10)                               
        self.objects_pub = self.create_publisher(DetectedObjectArray, '/detected_objects', 10)                 
        self.bridge = CvBridge()                                                                               
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_250)                            
        self.aruco_params = cv2.aruco.DetectorParameters()                                                     
        self.charuco_board = cv2.aruco.CharucoBoard(                                                           
            (5, 7),  # cols, rows (according to field: 5 columns, 7 rows)                                      
            0.25,    # square length in meters (250 mm)                                                        
            0.20,    # marker length in meters (200 mm)                                                        
            self.aruco_dict                                                                                    
        )                                                                                                      
        self.camera_matrix = None                                                                              
        self.dist_coeffs = None                                                                                
        self.load_calibration()                                                                                
                                                                                                               
    def load_calibration(self):                                                                                
        calibration_file = self.get_parameter('calibration_file').value                                        
        config_dir = os.path.join(get_package_share_directory('ros2_robot_platform'), 'config')                
        calib_path = os.path.join(config_dir, calibration_file)                                                
                                                                                                               
        if os.path.exists(calib_path):                                                                         
            self.get_logger().info(f'Loading calibration from {calib_path}')                                   
            with open(calib_path, 'r') as f:                                                                   
                calib = yaml.safe_load(f)                                                                      
                                                                                                               
            # Load camera matrix                                                                               
            cam_data = calib.get('camera_matrix', {}).get('data', [800., 0., 320., 0., 800., 240., 0., 0., 1.])
            self.camera_matrix = np.array(cam_data).reshape(3,3)                                               
                                                                                                               
            # Load distortion coefficients                                                                     
            dist_data = calib.get('distortion_coefficients', {}).get('data', [0., 0., 0., 0., 0.])             
            self.dist_coeffs = np.array(dist_data).reshape(-1,1)                                               
        else:                                                                                                  
            self.get_logger().warn(f'Calibration file {calib_path} not found. Using default values.')          
            self.camera_matrix = np.array([[800., 0., 320.],                                                   
                                           [0., 800., 240.],                                                   
                                           [0., 0., 1.]])                                                      
            self.dist_coeffs = np.zeros((5,1))                                                                 
                                                                                                               
    def image_callback(self, msg):                                                                             
        try:                                                                                                   
            cv_image = self.bridge.imgmsg_to_cv2(msg, 'bgr8')                                                  
        except Exception as e:                                                                                 
            self.get_logger().error(f'Failed to convert image: {e}')                                           
            return                                                                                             
                                                                                                               
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)                                                      
                                                                                                               
        use_charuco = self.get_parameter('use_charuco').value                                                  
        pose_array = PoseArray()                                                                               
        pose_array.header = msg.header                                                                         
                                                                                                               
        if use_charuco:                                                                                        
            # Detect ChArUco board for precise positioning                                                     
            corners, ids, rejected = cv2.aruco.detectMarkers(gray, self.aruco_dict,                            
parameters=self.aruco_params)                                                                                  
            if ids is not None:                                                                                
                ret, charuco_corners, charuco_ids = cv2.aruco.interpolateCornersCharuco(                       
                    corners, ids, gray, self.charuco_board)                                                    
                if ret > 0:                                                                                    
                    ret, rvec, tvec = cv2.aruco.estimatePoseCharucoBoard(                                      
                        charuco_corners, charuco_ids, self.charuco_board,                                      
                        self.camera_matrix, self.dist_coeffs, None, None)                                      
                    if ret:                                                                                    
                        # Publish robot pose relative to board                                                 
                        pose = Pose()                                                                          
                        pose.position.x = float(tvec[0][0])                                                    
                        pose.position.y = float(tvec[1][0])                                                    
                        pose.position.z = float(tvec[2][0])                                                    
                        # Convert rotation vector to quaternion (simplified)                                   
                        pose.orientation.w = 1.0                                                               
                        pose_array.poses.append(pose)                                                          
                        cv2.aruco.drawDetectedCornersCharuco(cv_image, charuco_corners, charuco_ids)           
                        cv2.drawFrameAxes(cv_image, self.camera_matrix, self.dist_coeffs, rvec, tvec, 0.1)     
        else:                                                                                                  
            # Fallback to single markers                                                                       
            corners, ids, rejected = cv2.aruco.detectMarkers(gray, self.aruco_dict,                            
parameters=self.aruco_params)                                                                                  
            if ids is not None:                                                                                
                rvecs, tvecs, _ = cv2.aruco.estimatePoseSingleMarkers(corners, 0.05, self.camera_matrix,       
self.dist_coeffs)                                                                                              
                for i in range(len(ids)):                                                                      
                    pose = Pose()                                                                              
                    pose.position.x = float(tvecs[i][0][0])                                                    
                    pose.position.y = float(tvecs[i][0][1])                                                    
                    pose.position.z = float(tvecs[i][0][2])                                                    
                    pose.orientation.w = 1.0                                                                   
                    pose_array.poses.append(pose)                                                              
                    cv2.aruco.drawDetectedMarkers(cv_image, corners, ids)                                      
                    cv2.aruco.drawAxis(cv_image, self.camera_matrix, self.dist_coeffs, rvecs[i], tvecs[i],     
0.03)                                                                                                          
                                                                                                               
        self.pose_pub.publish(pose_array)                                                                      
                                                                                                               
        # TODO: Add object detection (cubes, cylinders, figurines) using color/contour analysis                
        # For now, publish empty object array                                                                  
        objects_msg = DetectedObjectArray()                                                                    
        objects_msg.header = msg.header                                                                        
                                                                                                               
        # Convert to HSV for color detection                                                                   
        hsv = cv2.cvtColor(cv_image, cv2.COLOR_BGR2HSV)                                                        
                                                                                                               
        # Detect blue cubes (CUBE_BLUE)                                                                        
        lower_blue = np.array([100, 150, 50])                                                                  
        upper_blue = np.array([140, 255, 255])                                                                 
        blue_mask = cv2.inRange(hsv, lower_blue, upper_blue)                                                   
                                                                                                               
        # Find contours in blue mask                                                                           
        contours, _ = cv2.findContours(blue_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)                  
        for contour in contours:                                                                               
            area = cv2.contourArea(contour)                                                                    
            if area > 100:  # Minimum area threshold                                                           
                # Get bounding box                                                                             
                x, y, w, h = cv2.boundingRect(contour)                                                         
                # Calculate center (in pixel coordinates)                                                      
                center_x = x + w // 2                                                                          
                center_y = y + h // 2                                                                          
                                                                                                               
                # Create detected object                                                                       
                obj = DetectedObject()                                                                         
                obj.type = DetectedObject.CUBE_BLUE                                                            
                obj.pose.position.x = float(center_x)                                                          
                obj.pose.position.y = float(center_y)                                                          
                obj.pose.position.z = 0.0                                                                      
                obj.pose.orientation.w = 1.0                                                                   
                obj.confidence = min(1.0, area / 1000.0)                                                       
                objects_msg.objects.append(obj)                                                                
                                                                                                               
                # Draw for visualization                                                                       
                cv2.rectangle(cv_image, (x, y), (x+w, y+h), (255, 0, 0), 2)                                    
                cv2.putText(cv_image, 'Blue Cube', (x, y-10),                                                  
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)                                      
                                                                                                               
        self.objects_pub.publish(objects_msg)                                                                     
                                                                                                               
        show = self.get_parameter('show_image').value                                                          
        if show:                                                                                               
            cv2.imshow('Camera View', cv_image)                                                                
            cv2.waitKey(1)                                                                                     
                                                                                                               
def main(args=None):                                                                                           
    rclpy.init(args=args)                                                                                      
    node = CameraDetector()                                                                                    
    rclpy.spin(node)                                                                                           
    node.destroy_node()                                                                                        
    rclpy.shutdown()                                                                                           
                                                                                                               
if __name__ == '__main__':                                                                                     
    main()  