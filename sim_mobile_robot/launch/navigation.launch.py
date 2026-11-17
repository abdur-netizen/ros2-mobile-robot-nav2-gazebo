import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    package_share = get_package_share_directory('sim_mobile_robot')
    nav2_share = get_package_share_directory('nav2_bringup')
    sim_launch = os.path.join(package_share, 'launch', 'sim_robot.launch.py')
    params_file = os.path.join(package_share, 'config', 'nav2_params.yaml')
    default_map = os.path.join(package_share, 'maps', 'small_maze.yaml')
    nav2_rviz = os.path.join(nav2_share, 'rviz', 'nav2_default_view.rviz')

    map_arg = DeclareLaunchArgument(
        'map', default_value=default_map,
        description='Full path to the occupancy-grid map YAML file.')
    params_arg = DeclareLaunchArgument(
        'params_file', default_value=params_file,
        description='Full path to the Nav2 parameter YAML file.')
    rviz_arg = DeclareLaunchArgument(
        'use_rviz', default_value='true',
        description='Start the Nav2 RViz interface.')

    simulation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(sim_launch),
        launch_arguments={'start_rviz': 'false'}.items(),
    )

    localization = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav2_share, 'launch', 'localization_launch.py')),
        launch_arguments={
            'map': LaunchConfiguration('map'),
            'params_file': LaunchConfiguration('params_file'),
            'use_sim_time': 'True',
        }.items(),
    )

    navigation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav2_share, 'launch', 'navigation_launch.py')),
        launch_arguments={
            'params_file': LaunchConfiguration('params_file'),
            'use_sim_time': 'True',
        }.items(),
    )

    rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='nav2_rviz',
        output='screen',
        arguments=['-d', nav2_rviz],
        parameters=[{'use_sim_time': True}],
        condition=IfCondition(LaunchConfiguration('use_rviz')),
    )

    return LaunchDescription([
        map_arg,
        params_arg,
        rviz_arg,
        simulation,
        localization,
        navigation,
        rviz,
    ])
