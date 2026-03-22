import os                                                                                                      
from launch import LaunchDescription                                                                           
from launch.actions import ExecuteProcess, DeclareLaunchArgument                                               
from launch.substitutions import LaunchConfiguration                                                           
from ament_index_python.packages import get_package_share_directory                                            
                                                                                                               
def generate_launch_description():                                                                             
    # Argument for specifying the backend script path                                                          
    backend_script_arg = DeclareLaunchArgument(                                                                
        'backend_script',                                                                                      
        default_value='',                                                                                      
        description='Path to backend.py (if not provided, will search)'                                        
    )                                                                                                          
                                                                                                               
    backend_script = LaunchConfiguration('backend_script')                                                     
                                                                                                               
    # If not provided, search in install then source directory                                                 
    pkg_share = get_package_share_directory('ros2_robot_platform')                                             
    web_dir_install = os.path.join(pkg_share, 'web_teleop')                                                    
    backend_install = os.path.join(web_dir_install, 'backend.py')                                              
                                                                                                               
    # Determine which script to use                                                                            
    import sys                                                                                                 
    if os.path.exists(backend_install):                                                                        
        script_to_run = backend_install                                                                        
    else:                                                                                                      
        # Fallback to source directory (assuming colcon workspace layout)                                      
        src_dir = os.path.join(pkg_share, '..', '..', 'src', 'ros2_robot_platform', 'web_teleop')              
        script_to_run = os.path.join(src_dir, 'backend.py')                                                    
        if not os.path.exists(script_to_run):                                                                  
            # Last resort: current directory                                                                   
            script_to_run = os.path.join(os.getcwd(), 'web_teleop', 'backend.py')                              
                                                                                                               
    backend_node = ExecuteProcess(                                                                             
        cmd=[sys.executable, script_to_run],                                                                   
        output='screen'                                                                                        
    )                                                                                                          
                                                                                                               
    return LaunchDescription([                                                                                 
        backend_script_arg,                                                                                    
        backend_node,                                                                                          
    ])                 