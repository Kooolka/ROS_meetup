import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    config_dir = os.path.join(get_package_share_directory('ros2_robot_platform'), 'config')
    
    camera_node = Node(
        package='ros2_robot_platform',
        executable='camera_detector',
        name='camera_detector',
        parameters=[os.path.join(config_dir, 'camera_calibration.yaml'),
                    {'show_image': False}],
        output='screen'
    )
    
    navigator_node = Node(
        package='ros2_robot_platform',
        executable='aruco_navigator',
        name='aruco_navigator',
        parameters=[os.path.join(config_dir, 'aruco_tags.yaml')],
        output='screen'
    )
    
    planner_node = Node(
        package='ros2_robot_platform',
        executable='path_planner',
        name='path_planner',
        output='screen'
    )
    
    bridge_node = Node(
        package='ros2_robot_platform',
        executable='serial_bridge',
        name='serial_bridge',
        parameters=[{'port': '/dev/ttyUSB0', 'baudrate': 115200}],
        output='screen'
    )
    
    arm_node = Node(
        package='ros2_robot_platform',
        executable='arm_controller',
        name='arm_controller',
        parameters=[{'port': '/dev/ttyUSB0', 'baudrate': 115200}],
        output='screen'
    )
    
    return LaunchDescription([
        camera_node,
        navigator_node,
        planner_node,
        bridge_node,
        arm_node
    ])
