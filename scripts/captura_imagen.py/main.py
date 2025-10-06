#!/usr/bin/env python3
import os
from picamera import PiCamera
from time import sleep

def capture_image(output_path: str = "../imagenes/ultima.jpg",
                  resolution: tuple = (224, 224)) -> str:
    """
    Captura una imagen con la cámara OV5647 y la guarda.
    Devuelve la ruta al archivo generado.
    """
    # Asegurar que la carpeta existe
    folder = os.path.dirname(__file__) + "/" + os.path.dirname(output_path)
    os.makedirs(folder, exist_ok=True)

    # Configurar cámara
    camera = PiCamera()
    camera.resolution = resolution
    camera.start_preview()
    sleep(2)             # Tiempo para ajustar la exposición
    full_path = os.path.abspath(os.path.join(os.path.dirname(__file__), output_path))
    camera.capture(full_path)
    camera.close()
    return full_path

if __name__ == "__main__":
    img_path = capture_image()
    print(f"✔ Imagen capturada y guardada en: {img_path}")
