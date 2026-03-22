import os                                                                                                      
from launch import LaunchDescription                                                                           
from launch_ros.actions import Node                                                                            
from launch.actions import ExecuteProcess                                                                      
                                                                                                               
def generate_launch_description():                                                                             
    # Path to the web_teleop directory inside the package                                                      
    pkg_dir = os.path.join(os.getcwd(), 'src/ros2_robot_platform')                                             
    web_dir = os.path.join(pkg_dir, 'web_teleop')                                                              
                                                                                                               
    # Ensure the directory exists (will be created by user)                                                    
    # For now, we'll just launch the backend if it's present                                                   
    backend_script = os.path.join(web_dir, 'backend.py')                                                       
                                                                                                               
    backend_node = ExecuteProcess(                                                                             
        cmd=['python3', backend_script],                                                                       
        output='screen'                                                                                        
    )                                                                                                          
                                                                                                               
    return LaunchDescription([                                                                                 
        backend_node,                                                                                          
    ])                                                                                                         