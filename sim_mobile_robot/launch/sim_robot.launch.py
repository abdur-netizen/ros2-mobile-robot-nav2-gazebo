import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory('sim_mobile_robot')
    urdf_file = os.path.join(pkg_share, 'urdf', 'sim_robot_org.urdf')
    world_file = os.path.join(pkg_share, 'worlds', 'small_maze.sdf')
    rviz_config_file = os.path.join(pkg_share, 'rviz', 'default.rviz')

    with open(urdf_file, 'r', encoding='utf-8') as urdf_stream:
        robot_description_config = urdf_stream.read()

    start_rviz_arg = DeclareLaunchArgument(
        'start_rviz', default_value='true',
        description='Start the basic RViz view with the simulator.')

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description_config,
            'use_sim_time': True,
        }],
    )

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('ros_gz_sim'),
                'launch', 'gz_sim.launch.py')),
        launch_arguments={'gz_args': f'-r {world_file}'}.items(),
    )

    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-topic', 'robot_description',
            '-name', 'sim_mobile_robot',
            '-x', '0.0', '-y', '0.0', '-z', '0.2',
        ],
        output='screen',
    )

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/clock@rosgraph_msgs/msg/Clock[ignition.msgs.Clock',
            '/cmd_vel@geometry_msgs/msg/Twist]ignition.msgs.Twist',
            '/odom@nav_msgs/msg/Odometry[ignition.msgs.Odometry',
            '/tf@tf2_msgs/msg/TFMessage[ignition.msgs.Pose_V',
            '/scan@sensor_msgs/msg/LaserScan[ignition.msgs.LaserScan',
            '/world/maze_world/model/sim_mobile_robot/joint_state'
            '@sensor_msgs/msg/JointState[ignition.msgs.Model',
        ],
        remappings=[
            ('/world/maze_world/model/sim_mobile_robot/joint_state',
             '/joint_states'),
        ],
        output='screen',
    )

    rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config_file],
        parameters=[{'use_sim_time': True}],
        condition=IfCondition(LaunchConfiguration('start_rviz')),
    )

    return LaunchDescription([
        start_rviz_arg,
        robot_state_publisher,
        gazebo,
        spawn_robot,
        bridge,
        rviz,
    ])
