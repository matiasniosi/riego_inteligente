#!/usr/bin/env python3
import os
import re
import csv
import time
import serial
from datetime import datetime

class ArduinoSerial:
    def __init__(self,
                 port: str = "/dev/ttyACM0",
                 baudrate: int = 9600,
                 timeout: float = 1.0):
        """
        Inicializa la conexión serial con Arduino
        y prepara la ruta al archivo CSV de historial.
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout

        # Directorio base del proyecto
        base_dir = os.path.abspath(os.path.join(__file__, "..", ".."))
        self.csv_path = os.path.join(base_dir, "datos", "historial_riego.csv")

        # Crear carpeta y CSV si no existen
        os.makedirs(os.path.dirname(self.csv_path), exist_ok=True)
        if not os.path.isfile(self.csv_path):
            with open(self.csv_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Fecha y Hora", "Humedad (raw)", "Válvula", "Observaciones"])

        # Abrir conexión serial
        self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
        # Pequeña espera para estabilizar
        time.sleep(2)

    def read_serial(self) -> dict:
        """
        Lee una línea desde el serial y parsea humedad y estado de válvula.
        Retorna un dict con keys: humedad, valvula.
        """
        raw = self.ser.readline().decode("utf-8", errors="ignore").strip()
        # Esperar hasta recibir un string válido
        if not raw or "|" not in raw:
            return {}

        # Ejemplo de raw: "Humedad: 512 | Válvula: ON"
        match = re.search(r"Humedad:\s*(\d+)\s*\|\s*Válvula:\s*(ON|OFF)", raw)
        if not match:
            return {}

        humedad = int(match.group(1))
        valvula = match.group(2)
        return {"humedad": humedad, "valvula": valvula}

    def append_to_csv(self, record: dict):
        """
        Añade un registro al CSV de historial.
        """
        with open(self.csv_path, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                record["timestamp"],
                record["humedad"],
                record["valvula"],
                record.get("observaciones", "")
            ])

    def send_command(self, command: str):
        """
        Envía un comando al Arduino y agrega observación.
        command debe ser 'VALVULA ON' o 'VALVULA OFF'
        """
        cmd = command.strip() + "\n"
        self.ser.write(cmd.encode("utf-8"))

    def run_loop(self):
        """
        Loop principal: lee datos, guarda en CSV y muestra por consola.
        Permite ingresar comandos manuales en la consola.
        """
        print("Iniciando lectura serial. Presioná Ctrl+C para detener.")
        try:
            while True:
                data = self.read_serial()
                if data:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    record = {
                        "timestamp": timestamp,
                        "humedad": data["humedad"],
                        "valvula": data["valvula"]
                    }
                    self.append_to_csv(record)
                    print(f"[{timestamp}] Humedad={data['humedad']} | Válvula={data['valvula']}")

                # Chequear si el usuario escribió un comando
                if self.ser.in_waiting == 0 and os.isatty(0):
                    comando = input("Comando manual (ON/OFF/ENTER para continuar): ").strip().upper()
                    if comando == "ON":
                        self.send_command("VALVULA ON")
                        print(">> Enviado: VALVULA ON")
                    elif comando == "OFF":
                        self.send_command("VALVULA OFF")
                        print(">> Enviado: VALVULA OFF")
        except KeyboardInterrupt:
            print("\nDetenido por usuario.")
        finally:
            self.ser.close()

if __name__ == "__main__":
    # Punto de entrada para pruebas
    arduino = ArduinoSerial()
    arduino.run_loop()
