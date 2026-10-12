#!/usr/bin/env python3
"""Procesa imágenes de la cámara y publica una confirmación de botella.

Flujo: Image de ROS -> imagen BGR de OpenCV -> máscara binaria de la región
de interés -> confirmación Bool y registro en un archivo de texto.
"""

import time

import cv2
import numpy as np
import rclpy
from cv_bridge import CvBridge, CvBridgeError
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image
from std_msgs.msg import Bool


def detection(I, kernel=35, th=140, kernel2=7, iter=5):
    """Devuelve una máscara mono8 con las zonas claras que superan los filtros.

    I es la imagen BGR. kernel controla el suavizado, th el umbral de brillo,
    kernel2 el tamaño del elemento de erosión e iter sus repeticiones.
    """
    # La escala de grises permite comparar brillo sin considerar el color.
    # El desenfoque gaussiano atenúa variaciones pequeñas antes del umbral.
    gray = cv2.cvtColor(I, cv2.COLOR_BGR2GRAY)
    gauss_filter = cv2.GaussianBlur(gray, (kernel, kernel), 5)

    # La región de interés es un trapecio definido en píxeles de la imagen
    # original. Estas coordenadas son fijas; no se escalan con la resolución.
    height = 1020
    top = 600
    polygons = np.array([[(250, height), (1500, height), (1250, top), (400, top)]])
    roi = np.zeros_like(gauss_filter)
    # El interior blanco del trapecio conserva los píxeles de esa región;
    # bitwise_and deja negro el resto, sin cambiar el tamaño de la imagen.
    cv2.fillPoly(roi, polygons, 255)
    mask_roi = cv2.bitwise_and(gauss_filter, roi)

    # Los píxeles que superan th quedan blancos (255); el resto, negros (0).
    # La erosión reduce las zonas blancas y elimina detalles pequeños.
    _, bw = cv2.threshold(mask_roi, th, 255, cv2.THRESH_BINARY)
    k = np.ones((kernel2, kernel2), np.uint8)
    erode = cv2.erode(bw, k, iterations=iter)
    return erode


def bottle_confirmed(I, count_ones, count_zeros, start_time):
    """Actualiza la confirmación y conserva el estado entre procesamientos.

    msg indica la confirmación mantenida; flag indica si la máscara actual
    contiene píxeles blancos. La confirmación se mantiene durante ausencias
    breves y se desactiva tras más de tres segundos sin detección.
    """
    # Al detectar píxeles blancos, confirmar y cancelar el tiempo de ausencia.
    if cv2.countNonZero(I) > 0:
        count_ones += 1
        count_zeros = 0
        msg = True
        start_time = None
        flag = 1
    else:
        flag = 0
        # Solo mantener la confirmación si antes hubo una detección positiva.
        if count_ones != 0:
            count_zeros += 1
            msg = True
            if start_time is None:
                # El plazo comienza en el primer procesamiento sin detección.
                start_time = time.time()
            elif time.time() - start_time > 3:
                # Una ausencia sostenida reinicia contadores y confirmación.
                msg = False
                start_time = None
                count_ones = 0
                count_zeros = 0
        else:
            start_time = None
            msg = False
            count_zeros = 0

    return msg, count_ones, count_zeros, start_time, flag


class BottleDetectionNode(Node):
    """Recibe imágenes y procesa el último frame cada 0,1 segundos."""

    def __init__(self):
        super().__init__('camera_node_image_proccesing')
        # Parámetros modificables con --ros-args -p nombre:=valor.
        # El launch del paquete usa /camera/image_raw; al usarlo, asignar
        # image_topic:=/camera/image_raw para conectar esta suscripción.
        self.declare_parameter('image_topic', '/usb_cam/image_raw')
        # Se conserva la ruta original. Su carpeta debe existir y permitir
        # escritura; data_file permite elegir una ruta válida en este equipo.
        self.declare_parameter('data_file', '/home/utec/data_bottle.txt')

        # CvBridge convierte entre sensor_msgs/Image y arrays de OpenCV.
        self.bridge = CvBridge()
        # Esta imagen provisional de dos dimensiones evita procesar antes
        # de recibir el primer frame BGR válido de tres dimensiones.
        self.image = np.zeros((10, 10))
        # El perfil de sensores acepta imágenes con entrega best effort;
        # así puede recibir tanto de cámaras best effort como reliable.
        self.isub = self.create_subscription(
            Image,
            self.get_parameter('image_topic').value,
            self.image_callback,
            qos_profile_sensor_data,
        )
        # Salidas: máscara mono8 para visualizar y Bool para otros nodos.
        # Los enteros 10 y 1 indican la profundidad de las colas de mensajes.
        self.pubimg = self.create_publisher(Image, 'image_proccesed', 10)
        self.pub = self.create_publisher(Bool, 'bottle_confirmation', 1)
        self.pub_msg = Bool(data=False)
        # Estado de la detección, conservado entre llamadas del temporizador.
        self.flag = 0
        self.count_ones = 0
        self.count_zeros = 0
        self.start_time = None
        # t es tiempo acumulado nominal a 10 Hz, no tiempo real transcurrido.
        self.t = 0.0
        self.dt = 1.0 / 10
        # El modo 'w' crea el registro o reemplaza su contenido al iniciar.
        self.data = open(self.get_parameter('data_file').value, 'w')
        # El executor invoca process_image a 10 Hz, independientemente de
        # la frecuencia de llegada de las imágenes de la cámara.
        self.timer = self.create_timer(self.dt, self.process_image)
        self.get_logger().debug('Starting image processing node')

    def image_callback(self, img):
        """Guarda el último frame recibido, convertido a canales BGR de 8 bits."""
        try:
            self.image = self.bridge.imgmsg_to_cv2(img, 'bgr8')
        except CvBridgeError as e:
            self.get_logger().debug(str(e))
            print(e)

    def get_image(self):
        """Devuelve el último frame guardado por la suscripción."""
        return self.image

    def process_image(self):
        """Procesa la imagen disponible, publica salidas y registra el estado."""
        timestamp = time.strftime('%H%M%S')
        I = self.get_image()
        try:
            if len(I.shape) == 3 and I.shape[2] == 3:
                # Solo procesar imágenes con tres canales de color.
                I = detection(I)
                # La función devuelve tanto el resultado como el estado
                # que necesitará la siguiente llamada del temporizador.
                (
                    self.pub_msg.data,
                    self.count_ones,
                    self.count_zeros,
                    self.start_time,
                    self.flag,
                ) = bottle_confirmed(
                    I, self.count_ones, self.count_zeros, self.start_time
                )
                # mono8 representa una máscara de un canal, con valores
                # entre 0 y 255, lista para publicar como Image de ROS.
                self.pubimg.publish(self.bridge.cv2_to_imgmsg(I, 'mono8'))
        except CvBridgeError as e:
            self.get_logger().debug(str(e))
            print(e)

        # Columnas: tiempo nominal, hora HHMMSS, confirmación y detección
        # actual. La confirmación también se publica si no hay frame válido.
        self.data.write(
            f'{self.t} {timestamp} {self.pub_msg.data} {self.flag}\n'
        )
        self.pub.publish(self.pub_msg)
        self.t += self.dt

    def destroy_node(self):
        """Cierra el registro para guardar los datos pendientes al terminar."""
        self.data.close()
        return super().destroy_node()


def main(args=None):
    """Inicializa ROS 2 y atiende callbacks hasta recibir una señal de cierre."""
    rclpy.init(args=args)
    node = None
    try:
        node = BottleDetectionNode()
        # spin atiende los mensajes de la suscripción y el temporizador.
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        # Liberar archivo y recursos del nodo incluso al cerrar con Ctrl+C.
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
