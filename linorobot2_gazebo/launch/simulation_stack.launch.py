from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch.conditions import IfCondition
from launch_ros.substitutions import FindPackageShare
from launch_ros.actions import Node


def generate_launch_description():
    gazebo_launch = PathJoinSubstitution([
        FindPackageShare('linorobot2_gazebo'), 'launch', 'gazebo.launch.py'
    ])
    navigation_launch = PathJoinSubstitution([
        FindPackageShare('linorobot2_navigation'), 'launch', 'navigation.launch.py'
    ])

    return LaunchDescription([
        DeclareLaunchArgument(
            'world',
            default_value=PathJoinSubstitution([
                FindPackageShare('linorobot2_gazebo'), 'worlds', 'playground.world'
            ]),
        ),
        DeclareLaunchArgument(
            'map',
            default_value=PathJoinSubstitution([
                FindPackageShare('linorobot2_navigation'), 'maps', 'playground.yaml'
            ]),
        ),
        DeclareLaunchArgument('robot_base', default_value='4wd'),
        DeclareLaunchArgument('rviz', default_value='true'),
        DeclareLaunchArgument('rosbridge', default_value='true'),
        DeclareLaunchArgument('rosbridge_port', default_value='9090'),
        DeclareLaunchArgument('perception_gateway', default_value='true'),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(gazebo_launch),
            launch_arguments={
                'robot_base': LaunchConfiguration('robot_base'),
                'world': LaunchConfiguration('world'),
                'rosbridge': LaunchConfiguration('rosbridge'),
                'rosbridge_port': LaunchConfiguration('rosbridge_port'),
            }.items(),
        ),
        Node(
            package='linorobot2_gazebo',
            executable='codex_perception_gateway.py',
            name='codex_perception_gateway',
            output='screen',
            condition=IfCondition(LaunchConfiguration('perception_gateway')),
            parameters=[{'use_sim_time': True}],
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(navigation_launch),
            launch_arguments={
                'sim': 'true',
                'rviz': LaunchConfiguration('rviz'),
                'map': LaunchConfiguration('map'),
            }.items(),
        ),
    ])
