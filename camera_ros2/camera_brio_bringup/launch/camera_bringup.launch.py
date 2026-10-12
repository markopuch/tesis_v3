"""Inicia el controlador USB de la cámara Brio con el YAML del paquete."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    """Construye las acciones que ejecutará el comando ros2 launch."""

    # Buscar el YAML en el paquete instalado evita depender del directorio
    # desde el que el usuario ejecute el comando de lanzamiento.
    config_file = os.path.join(
        get_package_share_directory('camera_brio_bringup'),
        'config',
        'camera.yaml'
    )

    # El nodo se llama /camera/brio. Con los tópicos relativos de usb_cam,
    # la imagen se publica en /camera/image_raw, dentro de este namespace.
    # Este launch inicia el controlador; los tres scripts se ejecutan aparte.
    camera_node = Node(
        package='usb_cam',
        executable='usb_cam_node_exe',
        namespace='camera',
        name='brio',
        output='screen',
        parameters=[config_file]
    )

    # LaunchDescription agrupa las acciones que ROS 2 debe iniciar.
    return LaunchDescription([
        camera_node
    ])
