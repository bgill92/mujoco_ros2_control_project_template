"""my_robot in MuJoCo through mujoco_ros2_control.

Generate the MuJoCo model first (and again after any URDF change):
    pixi run gen-mjcf

Move the arm:
    ros2 action send_goal /arm_controller/follow_joint_trajectory \\
        control_msgs/action/FollowJointTrajectory "{trajectory: {joint_names: [joint1, joint2], \\
        points: [{positions: [1.0, 0.5], time_from_start: {sec: 2}}]}}"
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, Shutdown
from launch.conditions import IfCondition
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterFile, ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    share = FindPackageShare('my_robot_simulation')
    description_share = FindPackageShare('my_robot_description')
    controllers_file = PathJoinSubstitution([share, 'config', 'controllers.yaml'])

    robot_description = ParameterValue(
        Command([
            'xacro ', PathJoinSubstitution([description_share, 'urdf', 'my_robot.urdf.xacro']),
            ' ros2_control:=mujoco',
            ' mujoco_model:=', LaunchConfiguration('mujoco_model'),
            ' headless:=', LaunchConfiguration('headless'),
        ]),
        value_type=str,
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'headless', default_value='false',
            description='Run MuJoCo without its viewer window'),
        DeclareLaunchArgument(
            'rviz', default_value='true', description='Start RViz'),
        DeclareLaunchArgument(
            'mujoco_model',
            default_value=PathJoinSubstitution([share, 'mujoco', 'scene.xml']),
            description='MJCF scene'),
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{'robot_description': robot_description, 'use_sim_time': True}],
        ),
        # MuJoCo runs inside this controller manager. It reads robot_description from
        # the topic robot_state_publisher publishes.
        Node(
            package='mujoco_ros2_control',
            executable='ros2_control_node',
            emulate_tty=True,
            output='both',
            parameters=[{'use_sim_time': True}, ParameterFile(controllers_file)],
            on_exit=Shutdown(),
        ),
        # One spawner activates the controllers in order; separate spawners race.
        Node(
            package='controller_manager',
            executable='spawner',
            arguments=['joint_state_broadcaster', 'arm_controller', '--param-file', controllers_file],
        ),
        Node(
            package='rviz2',
            executable='rviz2',
            arguments=['-d', PathJoinSubstitution([description_share, 'rviz', 'my_robot.rviz'])],
            parameters=[{'use_sim_time': True}],
            condition=IfCondition(LaunchConfiguration('rviz')),
        ),
    ])
