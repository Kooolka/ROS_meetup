import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    # Get package share directory
    pkg_share = get_package_share_directory('ros2_robot_platform')
    
    # Path to backend.py in the installed package
    backend_script = os.path.join(pkg_share, 'web_teleop', 'backend.py')
    
    # If not found, try source directory (for development)
    if not os.path.exists(backend_script):
        # Assuming standard colcon workspace structure
        src_dir = os.path.join(pkg_share, '..', '..', 'src', 'ros2_robot_platform', 'web_teleop')
        backend_script = os.path.join(src_dir, 'backend.py')
    
    backend_node = ExecuteProcess(
        cmd=['python3', backend_script],
        output='screen'
    )
    
    return LaunchDescription([
        backend_node,
    ])
