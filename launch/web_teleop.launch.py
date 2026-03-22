import os                                                                                                      
from launch import LaunchDescription                                                                           
from launch_ros.actions import Node                                                                            
from launch.actions import ExecuteProcess                                                                      
from ament_index_python.packages import get_package_share_directory                                            
                                                                                                               
def generate_launch_description():                                                                             
    # Get the package share directory                                                                          
    pkg_share = get_package_share_directory('ros2_robot_platform')                                             
    web_dir = os.path.join(pkg_share, 'web_teleop')                                                            
                                                                                                               
    # Check if backend.py exists in the installed location                                                     
    backend_script = os.path.join(web_dir, 'backend.py')                                                       
                                                                                                               
    if not os.path.exists(backend_script):                                                                     
        # Fallback to source directory                                                                         
        src_dir = os.path.join(pkg_share, '../../src/ros2_robot_platform/web_teleop')                          
        backend_script = os.path.join(src_dir, 'backend.py')                                                   
                                                                                                               
    backend_node = ExecuteProcess(                                                                             
        cmd=['python3', backend_script],                                                                       
        output='screen',                                                                                       
        shell=True                                                                                             
    )                                                                                                          
                                                                                                               
    return LaunchDescription([                                                                                 
        backend_node,                                                                                          
    ])                     