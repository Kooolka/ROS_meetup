#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import numpy as np
import yaml
import os
from ament_index_python.packages import get_package_share_directory

class CameraCalibrator(Node):
    def __init__(self):
        super().__init__('camera_calibrator')
        self.subscription = self.create_subscription(
            Image,
            '/camera/image_raw',
            self.image_callback,
            10)
        self.bridge = CvBridge()
        
        # ChArUco board parameters
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_250)
        self.board = cv2.aruco.CharucoBoard((5,7), 0.25, 0.20, self.aruco_dict)
        self.aruco_params = cv2.aruco.DetectorParameters()
        
        self.calibration_data = []
        self.calibrated = False
        
    def image_callback(self, msg):
        cv_image = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        
        # Detect markers
        corners, ids, rejected = cv2.aruco.detectMarkers(gray, self.aruco_dict, parameters=self.aruco_params)
        
        if ids is not None:
            # Interpolate CharUco corners
            ret, charuco_corners, charuco_ids = cv2.aruco.interpolateCornersCharuco(
                corners, ids, gray, self.board)
            
            if ret > 0:
                # Draw detected corners
                cv2.aruco.drawDetectedCornersCharuco(cv_image, charuco_corners, charuco_ids)
                
                # Store for calibration
                self.calibration_data.append((charuco_corners, charuco_ids))
                self.get_logger().info(f'Detected {len(charuco_corners)} corners. Total samples: {len(self.calibration_data)}')
                
                # Calibrate when we have enough samples
                if len(self.calibration_data) >= 20 and not self.calibrated:
                    self.calibrate_camera(gray.shape[::-1])
        
        # Only show image if DISPLAY is available
        import os
        if 'DISPLAY' in os.environ:
            cv2.imshow('Calibration View', cv_image)
            key = cv2.waitKey(1)
            
            if key == ord('s') and self.calibrated:
                self.save_calibration()
            elif key == ord('q'):
                self.destroy_node()
                rclpy.shutdown()
        else:
            # If no display, just log
            self.get_logger().debug('Calibration in progress...')
    
    def calibrate_camera(self, image_size):
        all_corners = [data[0] for data in self.calibration_data]
        all_ids = [data[1] for data in self.calibration_data]
        
        ret, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.aruco.calibrateCameraCharuco(
            all_corners, all_ids, self.board, image_size, None, None)
        
        if ret:
            self.get_logger().info(f'Calibration successful! RMS error: {ret}')
            self.camera_matrix = camera_matrix
            self.dist_coeffs = dist_coeffs
            self.calibrated = True
            
            # Print parameters
            print("Camera matrix:")
            print(camera_matrix)
            print("\nDistortion coefficients:")
            print(dist_coeffs.flatten())
    
    def save_calibration(self):
        # Use package config directory
        config_dir = os.path.join(get_package_share_directory('ros2_robot_platform'), 'config')
        os.makedirs(config_dir, exist_ok=True)
        
        calibration_data = {
            'camera_matrix': {
                'rows': 3,
                'cols': 3,
                'data': self.camera_matrix.flatten().tolist()
            },
            'distortion_coefficients': {
                'rows': 1,
                'cols': len(self.dist_coeffs.flatten()),
                'data': self.dist_coeffs.flatten().tolist()
            },
            'image_width': 640,
            'image_height': 480
        }
        
        calib_path = os.path.join(config_dir, 'camera_calibration_accurate.yaml')
        with open(calib_path, 'w') as f:
            yaml.dump(calibration_data, f, default_flow_style=False)
        
        self.get_logger().info(f'Calibration saved to {calib_path}')

def main(args=None):
    rclpy.init(args=args)
    node = CameraCalibrator()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
