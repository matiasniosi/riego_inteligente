import serial
import time

# Ajustá el puerto según tu sistema (ej. COM3 en Windows)
arduino = serial.Serial('COM3', 9600)
time.sleep(2)  # Esperar a que el puerto se estabilice

def activar_riego():
    arduino.write(b'1')
    print("✅ Riego activado")

def desactivar_riego():
    arduino.write(b'0')
    print("🛑 Riego desactivado")

def leer_humedad():
    arduino.flushInput()
    linea = arduino.readline().decode().strip()
    if "Humedad:" in linea:
        valor = int(linea.split(":")[1])
        print(f"🌱 Humedad actual: {valor}")
        return valor
    return None
