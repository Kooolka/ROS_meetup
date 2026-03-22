from setuptools import setup                                                                                   
import os                                                                                                      
from glob import glob                                                                                          
                                                                                                               
package_name = 'ros2_robot_platform'                                                                           
                                                                                                               
setup(                                                                                                         
    name=package_name,                                                                                         
    version='0.1.0',                                                                                           
    packages=[package_name,                                                                                    
              f'{package_name}.vision_node',                                                                   
              f'{package_name}.control_node',                                                                  
              f'{package_name}.esp32_bridge',                                                                  
              f'{package_name}.game_manager'],                                                                 
    data_files=[                                                                                               
         ('share/ament_index/resource_index/packages',                                                          
            ['resource/' + package_name]),                                                                     
        ('share/' + package_name, ['package.xml']),                                                            
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),                                  
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),                                
        (os.path.join('share', package_name, 'firmware'), glob('firmware/*.cpp')),                             
        (os.path.join('share', package_name, 'firmware'), glob('firmware/*.h')),                               
        (os.path.join('share', package_name, 'firmware'), glob('firmware/*.ini')),                             
        (os.path.join('share', package_name, 'firmware'), glob('firmware/CMakeLists.txt')),                    
        (os.path.join('share', package_name, 'msg'), glob('msg/*.msg')),                                       
        (os.path.join('share', package_name, 'web_teleop'), glob('web_teleop/*.py')),                          
        (os.path.join('share', package_name, 'web_teleop'), glob('web_teleop/*.html')),                        
    ],                                                                                                          
    install_requires=['setuptools'],                                                                           
    zip_safe=True,                                                                                             
    maintainer='User',                                                                                         
    maintainer_email='user@example.com',                                                                       
    description='ROS2 package for robot with camera vision and ESP32 motor control',                           
    license='Apache-2.0',                                                                                      
    tests_require=['pytest'],                                                                                  
    entry_points={                                                                                             
        'console_scripts': [                                                                                   
            'camera_detector = ros2_robot_platform.vision_node.camera_detector:main',                          
            'aruco_navigator = ros2_robot_platform.vision_node.aruco_navigator:main',                          
            'path_planner = ros2_robot_platform.control_node.path_planner:main',                               
            'serial_bridge = ros2_robot_platform.esp32_bridge.serial_bridge:main',                             
            'arm_controller = ros2_robot_platform.control_node.arm_controller:main',                           
            'game_manager = ros2_robot_platform.game_manager.game_manager:main',                               
        ],                                                                                                     
    },                                                                                                         
)                            