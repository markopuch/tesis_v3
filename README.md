# tesis_v3

Guía de instalación y uso básico de la cámara USB **Logitech Brio** para el proyecto de tesis, con **ROS 2 Jazzy** en **Ubuntu 24.04**.

Aquí se reúnen los paquetes para capturar imágenes, visualizar el video e instalar la herramienta de calibración, junto con los comandos para identificar y configurar la cámara.

## 1. Instalar los paquetes de la cámara

Actualiza la lista de paquetes e instala el controlador y las herramientas de imagen:

```bash
sudo apt update
sudo apt install -y \
  ros-jazzy-usb-cam \
  ros-jazzy-image-transport \
  ros-jazzy-camera-info-manager \
  ros-jazzy-image-tools \
  ros-jazzy-rqt-image-view \
  v4l-utils
```

Cada paquete cumple una función dentro del flujo de captura:

| Paquete | Función |
| --- | --- |
| [usb_cam](https://index.ros.org/p/usb_cam/#jazzy) | Controlador para capturar imágenes de una cámara USB y publicarlas en ROS 2. |
| [image_transport](https://index.ros.org/p/image_transport/#jazzy) | Gestiona la publicación y recepción de imágenes mediante distintos transportes. |
| [camera_info_manager](https://index.ros.org/p/camera_info_manager/#jazzy) | Administra la información de calibración de la cámara. |
| [image_tools](https://index.ros.org/p/image_tools/#jazzy) | Proporciona herramientas para publicar y recibir imágenes. |
| `rqt_image_view` | Permite visualizar los tópicos de imagen en una ventana gráfica. |
| `v4l-utils` | Incluye utilidades para consultar los dispositivos de video de Linux. |

## 2. Cargar el entorno de ROS 2

Antes de utilizar los comandos de ROS 2, carga su entorno en la terminal:

```bash
source /opt/ros/jazzy/setup.bash
```

Para consultar si ROS 2 reconoce los paquetes instalados:

```bash
ros2 pkg list | grep -E 'usb_cam|image_transport|camera_info_manager|image_tools|rqt_image_view'
```

## 3. Identificar el dispositivo de la cámara

Conecta la Logitech Brio y consulta los dispositivos disponibles:

```bash
v4l2-ctl --list-devices
```

La salida relaciona el nombre de cada cámara con sus rutas `/dev/video*`. En el ejemplo de esta laptop se utiliza **`/dev/video4`**; reemplaza ese valor si tu cámara aparece con otra ruta.

## 4. Iniciar la captura y visualizar las imágenes

Para iniciar el controlador con su configuración predeterminada:

```bash
ros2 run usb_cam usb_cam_node_exe
```

Para utilizar la Brio indicando el dispositivo, una resolución de **640 × 480 píxeles** y una frecuencia de **30 FPS**, inicia el controlador con estos parámetros:

```bash
ros2 run usb_cam usb_cam_node_exe \
  --ros-args \
  -p video_device:=/dev/video4 \
  -p image_width:=640 \
  -p image_height:=480 \
  -p framerate:=30.0
```

Utiliza un único comando de arranque a la vez. Mantén abierta la terminal del controlador y, en **otra terminal**, carga el entorno y abre el visor:

```bash
source /opt/ros/jazzy/setup.bash
ros2 run rqt_image_view rqt_image_view
```

En la ventana del visor, selecciona el tópico de imagen publicado por la cámara para ver la captura.

## 5. Instalar la herramienta de calibración

La calibración permite estimar los parámetros ópticos de la cámara y la distorsión de la lente. El paquete [camera_calibration](https://index.ros.org/p/camera_calibration/#jazzy) proporciona una herramienta para realizar este proceso utilizando un tablero de ajedrez.

```bash
sudo apt update
sudo apt install ros-jazzy-camera-calibration
```

Este comando instala la herramienta; la calibración se realiza posteriormente con la cámara en funcionamiento y el patrón de calibración.
