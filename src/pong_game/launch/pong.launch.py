from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='pong_game',
            executable='pygame_pong',
            name='pygame_pong',
            output='screen'
        ),
        Node(
            package='pong_game',
            executable='visualizer',
            name='pong_visualizer',
            output='screen'
        ),
    ])
