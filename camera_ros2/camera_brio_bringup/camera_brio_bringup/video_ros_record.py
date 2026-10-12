#!/usr/bin/env python3
"""Graba en un archivo AVI las imágenes de un tópico de cámara de ROS 2."""

import time

import cv2
import numpy as np
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image
from cv_bridge import CvBridge, CvBridgeError


class Cam(Node):
    """Nodo que recibe imágenes, conserva la última y la escribe periódicamente."""

    def __init__(self, topic_name='/usb_cam/image_raw'):
        # Node proporciona los parámetros, suscripciones, temporizadores y logger
        # de ROS 2. Se conserva el nombre de nodo del código original.
        super().__init__('camera_node_1')

        # El parámetro image_topic permite elegir el tópico al lanzar el nodo.
        # Si no se configura, se utiliza /usb_cam/image_raw.
        self.declare_parameter('image_topic', topic_name)
        topic_name = self.get_parameter('image_topic').value

        # CvBridge convierte los mensajes Image de ROS a arrays de OpenCV.
        self.bridge = CvBridge()
        # Este array inicial no tiene tres canales: evita escribir antes de
        # recibir el primer fotograma válido de la cámara.
        self.image = np.zeros((10, 10))

        # El QoS para sensores utiliza entrega best effort, adecuada para flujos
        # de cámara que priorizan recibir imágenes recientes.
        self.isub = self.create_subscription(
            Image, topic_name, self.image_callback, qos_profile_sensor_data
        )

        # Resolución fija del video; debe coincidir con las imágenes recibidas.
        # Estos valores no se consultan automáticamente a la cámara.
        frame_width = 1920
        frame_height = 1080

        # XVID es el códec utilizado para comprimir los fotogramas del AVI.
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        # El nombre incorpora fecha y hora. Como no incluye una ruta absoluta,
        # el archivo se guarda en el directorio desde el que se ejecuta el nodo.
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        name = 'video_' + timestamp + '.avi'

        # 20.0 es la tasa de reproducción declarada para el archivo de video.
        self.out = cv2.VideoWriter(
            name, fourcc, 20.0, (frame_width, frame_height)
        )

        # El temporizador escribe la imagen disponible a 10 Hz (cada 0.1 s).
        # Esta frecuencia y los 20 FPS del archivo son valores independientes
        # conservados del original: el video reproduce los frames al doble
        # de la frecuencia con la que se escriben si el timer mantiene 10 Hz.
        freq = 10
        self.timer = self.create_timer(1.0 / freq, self.record_frame)
        self.get_logger().debug('Starting recording node')

    def image_callback(self, img):
        """Convierte cada mensaje recibido y actualiza la última imagen disponible."""
        try:
            # bgr8 produce tres canales de color de 8 bits en el orden BGR
            # que utiliza OpenCV. La imagen anterior se reemplaza por la nueva.
            self.image = self.bridge.imgmsg_to_cv2(img, 'bgr8')
        except CvBridgeError as e:
            # Si falla la conversión, se conserva la última imagen convertida.
            self.get_logger().debug(str(e))
            print(e)

    def get_image(self):
        """Devuelve la imagen almacenada sin esperar un nuevo mensaje."""
        return self.image

    def record_frame(self):
        """Escribe el último fotograma disponible cuando se activa el temporizador."""
        I = self.get_image()
        # Comprobar que el array tenga alto, ancho y tres canales de color.
        # Esta condición también descarta el array inicial antes de recibir datos.
        if len(I.shape) == 3 and I.shape[2] == 3:
            try:
                # Si aún no llegó otra imagen, se vuelve a escribir la última.
                self.out.write(I)
            except CvBridgeError as e:
                self.get_logger().debug(str(e))

    def destroy_node(self):
        """Detiene la escritura y cierra el archivo antes de destruir el nodo."""
        self.timer.cancel()
        # release finaliza el AVI y libera el recurso de OpenCV.
        self.out.release()
        return super().destroy_node()


def main(args=None):
    """Punto de entrada para ejecutar el nodo como script o console_script."""
    # Inicializar el contexto ROS 2 antes de crear el nodo.
    rclpy.init(args=args)
    cam = Cam()
    try:
        # spin atiende los mensajes de la cámara y las llamadas del temporizador.
        rclpy.spin(cam)
    except (KeyboardInterrupt, ExternalShutdownException):
        # Ctrl+C o un cierre externo permiten pasar a la limpieza de recursos.
        pass
    finally:
        # El cierre del nodo libera el archivo incluso si spin termina por error.
        cam.destroy_node()
        # Cerrar el contexto si no fue cerrado previamente desde fuera.
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
