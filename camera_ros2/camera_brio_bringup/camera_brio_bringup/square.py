#!/usr/bin/env python3
"""Recibe imágenes de la cámara y publica un polígono dibujado sobre ellas.

La recepción de imágenes y el procesamiento se atienden con ROS 2. El nodo
conserva el último fotograma recibido y lo procesa a una frecuencia de 10 Hz.
"""

import cv2
import numpy as np
import rclpy
from cv_bridge import CvBridge, CvBridgeError
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image


class Cam(Node):
    """Nodo que conecta los mensajes de imagen de ROS 2 con OpenCV."""

    def __init__(self):
        """Configura el tópico de entrada, la publicación y el temporizador."""
        super().__init__('camera_node_image_proccesing_1')
        # Este parámetro permite elegir el tópico de la cámara al iniciar el nodo.
        self.declare_parameter('image_topic', '/usb_cam/image_raw')
        topic_name = self.get_parameter('image_topic').value

        # CvBridge convierte entre sensor_msgs/Image y matrices de OpenCV.
        self.bridge = CvBridge()
        # Imagen provisional sin canales BGR: se omite hasta recibir un fotograma.
        self.image = np.zeros((10, 10))
        # El QoS de sensores usa entrega de mejor esfuerzo y una cola corta,
        # adecuada para recibir imágenes recientes de una cámara.
        self.isub = self.create_subscription(
            Image, topic_name, self.image_callback, qos_profile_sensor_data
        )
        # Publicar las imágenes procesadas; 10 es la profundidad de la cola.
        self.pubimg = self.create_publisher(Image, 'image_proccesed_squared', 10)
        # Cada 0,1 segundos se procesa el último fotograma disponible.
        self.timer = self.create_timer(1.0 / 10.0, self.process_image)
        self.get_logger().debug('Starting image processing node_1')

    def image_callback(self, img):
        """Convierte el mensaje recibido y guarda el último fotograma BGR."""
        try:
            # 'bgr8' corresponde a tres canales de 8 bits: azul, verde y rojo.
            # Cada mensaje reemplaza el fotograma guardado para el temporizador.
            self.image = self.bridge.imgmsg_to_cv2(img, 'bgr8')
        except CvBridgeError as e:
            self.get_logger().debug(str(e))
            print(e)

    def get_image(self):
        """Devuelve el fotograma que se recibió más recientemente."""
        return self.image

    def process_image(self):
        """Dibuja el polígono y publica el resultado como mensaje de ROS 2."""
        # Obtener y procesar la imagen a una frecuencia de 10 Hz.
        I = self.get_image()
        try:
            # Solo procesar matrices con los tres canales esperados para BGR.
            if len(I.shape) == 3 and I.shape[2] == 3:
                I = detection(I)
                # Convertir la imagen de OpenCV a Image antes de publicarla.
                self.pubimg.publish(self.bridge.cv2_to_imgmsg(I, 'bgr8'))
        except CvBridgeError as e:
            self.get_logger().debug(str(e))
            print(e)


def detection(I, kernel=35, th=140, kernel2=7, iter=5):
    """Dibuja el polígono heredado sobre una copia de la imagen de entrada.

    Los parámetros kernel, th, kernel2 e iter se conservan en la firma original,
    aunque este dibujo no los utiliza.
    """
    # Los vértices son coordenadas (x, y) en píxeles heredadas del código original.
    # No se ajustan automáticamente al ancho o al alto del fotograma recibido.
    height = 1020
    top = 600
    polygons = np.array([[(250, height), (1500, height), (1250, top), (400, top)]])
    # Trabajar sobre una copia evita dibujar sobre el fotograma guardado del nodo.
    n = I.copy()
    # Cerrar el polígono y dibujar su contorno azul en BGR, con grosor de 5 píxeles.
    square = cv2.polylines(n, [polygons], isClosed=True, color=(255, 0, 0), thickness=5)
    return square


def main(args=None):
    """Inicializa ROS 2, atiende los callbacks y libera los recursos al salir."""
    rclpy.init(args=args)
    cam = Cam()
    try:
        # spin mantiene activo el nodo y atiende la suscripción y el temporizador.
        rclpy.spin(cam)
    except (KeyboardInterrupt, ExternalShutdownException):
        # Permitir el cierre por Ctrl+C o por apagado externo del contexto ROS 2.
        pass
    finally:
        # Liberar el nodo y cerrar el contexto si sigue activo.
        cam.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
