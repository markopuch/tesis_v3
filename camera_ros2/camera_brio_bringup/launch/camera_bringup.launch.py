import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():

    config_file = os.path.join(
        get_package_share_directory('camera_brio_bringup'),
        'config',
        'camera.yaml'
    )

    camera_node = Node(
        package='usb_cam',
        executable='usb_cam_node_exe',
        namespace='camera',
        name='brio',
        output='screen',
        parameters=[config_file]
    )

    return LaunchDescription([
        camera_node
    ])