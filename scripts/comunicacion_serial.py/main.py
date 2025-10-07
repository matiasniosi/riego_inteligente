#!/usr/bin/env python3
import os
import re
import csv
import time
import serial
from datetime import datetime

class ArduinoSerial:
    def __init__(self,
                 port: str = "COM4",
                 baudrate: int = 9600,
                 timeout: float = 1.0):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout

        # Umbrales invertidos: valores altos = tierra seca
        self.umbral_seco = 900
        self.umbral_humedo = 600
        self.estado_valvula = "OFF"

        base_dir = os.path.abspath(os.path.join(__file__, "..", ".."))
        self.csv_path = os.path.join(base_dir, "datos", "historial_riego.csv")

        os.makedirs(os.path.dirname(self.csv_path), exist_ok=True)
        if not os.path.isfile(self.csv_path):
            with open(self.csv_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Fecha y Hora", "Humedad (raw)", "Válvula", "Observaciones"])

        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            time.sleep(2)
        except serial.SerialException as e:
            print(f"❌ Error al abrir el puerto {self.port}: {e}")
            exit(1)

    def read_serial(self) -> dict:
        raw = self.ser.readline().decode("utf-8", errors="ignore").strip()
        match = re.search(r"Humedad:\s*(\d+)\s*\|\s*Válvula:\s*(ON|OFF)", raw)
        if not match:
            return {}
        return {
            "humedad": int(match.group(1)),
            "valvula": match.group(2)
        }

    def append_to_csv(self, record: dict):
        with open(self.csv_path, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                record["timestamp"],
                record["humedad"],
                record["valvula"],
                record.get("observaciones", "")
            ])

    def send_command(self, command: str):
        self.ser.write((command.strip() + "\n").encode("utf-8"))

    def actualizar_valvula(self, estado: str, origen: str) -> str:
        if estado == "ON":
            self.send_command("VALVULA ON")
        else:
            self.send_command("VALVULA OFF")
        self.estado_valvula = estado
        return f"Riego {origen} {'activado' if estado == 'ON' else 'desactivado'}"

    def evaluar_riego(self, humedad: int) -> str:
        if humedad > self.umbral_seco and self.estado_valvula == "OFF":
            return self.actualizar_valvula("ON", "automático")
        elif humedad < self.umbral_humedo and self.estado_valvula == "ON":
            return self.actualizar_valvula("OFF", "automático")
        return "Lectura normal"

    def run_loop(self):
        print(f"📡 Conectado a {self.port}. Iniciando lectura serial...")
        try:
            while True:
                data = self.read_serial()
                if data:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    evento = self.evaluar_riego(data["humedad"])
                    record = {
                        "timestamp": timestamp,
                        "humedad": data["humedad"],
                        "valvula": self.estado_valvula,
                        "observaciones": f"Arduino Uno | {evento}"
                    }
                    self.append_to_csv(record)
                    print(f"[{timestamp}] Humedad={data['humedad']} | Válvula={self.estado_valvula} → {evento}")

                if self.ser.in_waiting == 0 and os.isatty(0):
                    comando = input("Comando manual (ON/OFF/ENTER para continuar): ").strip().upper()
                    if comando == "ON":
                        evento = self.actualizar_valvula("ON", "manual")
                        print(f">> Enviado: VALVULA ON → {evento}")
                    elif comando == "OFF":
                        evento = self.actualizar_valvula("OFF", "manual")
                        print(f">> Enviado: VALVULA OFF → {evento}")
        except KeyboardInterrupt:
            print("\n🛑 Lectura detenida por el usuario.")
        finally:
            self.ser.close()

if __name__ == "__main__":
    arduino = ArduinoSerial()
    arduino.run_loop()
