import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'camera_brio_bringup'

# Metadatos e instrucciones de instalación del paquete Python para colcon.
setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    # Instalar el marcador de ament, el manifiesto, los launch y los YAML
    # para que ROS 2 pueda encontrarlos en el directorio share del paquete.
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='marko',
    maintainer_email='40008292+markopuch@users.noreply.github.com',
    description='TODO: Package description',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    # Cada entrada expone main como ejecutable para:
    # ros2 run camera_brio_bringup <nombre_del_script>
    entry_points={
        'console_scripts': [
            'bottle_detection = camera_brio_bringup.bottle_detection:main',
            'square = camera_brio_bringup.square:main',
            'video_ros_record = camera_brio_bringup.video_ros_record:main',
        ],
    },
)
