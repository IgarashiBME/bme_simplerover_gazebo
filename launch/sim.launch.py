"""Launch Gazebo Harmonic simulation with the simple rover."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    ExecuteProcess,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node


def generate_launch_description():
    pkg_dir = get_package_share_directory('bme_simplerover_gazebo')
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')

    # Paths
    urdf_file = os.path.join(pkg_dir, 'urdf', 'rover.urdf.xacro')
    world_file = os.path.join(pkg_dir, 'worlds', 'empty.sdf')
    bridge_config = os.path.join(pkg_dir, 'config', 'bridge.yaml')

    # Process xacro
    robot_description = os.popen(f'xacro {urdf_file}').read()

    # Launch arguments
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')

    # --- Gazebo Sim ---
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={
            'gz_args': f'-r {world_file}',
            'on_exit_shutdown': 'true',
        }.items(),
    )

    # --- Spawn Robot ---
    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-name', 'simple_rover',
            '-topic', 'robot_description',
            '-z', '0.1',
        ],
        output='screen',
    )

    # --- Robot State Publisher ---
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{
            'robot_description': robot_description,
            'use_sim_time': use_sim_time,
        }],
        output='screen',
    )

    # --- Fake GNSS (ground-truth position → UTM) ---
    fake_gnss = Node(
        package='bme_simplerover_gazebo',
        executable='fake_gnss_node.py',
        name='fake_gnss_node',
        parameters=[{
            'use_sim_time': use_sim_time,
            'origin_latitude': 35.0,
            'origin_longitude': 139.0,
            'origin_utm_easting': 500000.0,
            'origin_utm_northing': 3873000.0,
            'origin_height': 0.0,
        }],
        output='screen',
    )

    # --- ros_gz_bridge ---
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        parameters=[{
            'config_file': bridge_config,
            'use_sim_time': use_sim_time,
        }],
        output='screen',
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use simulation (Gazebo) clock',
        ),
        gz_sim,
        robot_state_publisher,
        spawn_robot,
        bridge,
        fake_gnss,
    ])
