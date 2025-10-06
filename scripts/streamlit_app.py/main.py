#!/usr/bin/env python3
import os
import sys
import pandas as pd
import streamlit as st

# Añadimos el root del proyecto al path para importar nuestros módulos
BASE_DIR = os.path.abspath(os.path.join(__file__, "..", ".."))
sys.path.append(BASE_DIR)

from scripts.comunicacion_serial import ArduinoSerial
from scripts.captura_imagen import capture_image
from scripts.clasificacion_ia import (
    load_model,
    load_labels,
    preprocess_image,
    predict,
)

# Rutas
CSV_PATH    = os.path.join(BASE_DIR, "datos", "historial_riego.csv")
IMAGE_PATH  = os.path.join(BASE_DIR, "imagenes", "ultima.jpg")
MODEL_PATH  = os.path.join(BASE_DIR, "modelo", "modelo.tflite")
LABELS_PATH = os.path.join(BASE_DIR, "modelo", "labels.txt")

# Inicializo Arduino-Serial y TensorFlow Lite
arduino = ArduinoSerial()
interpreter = load_model(MODEL_PATH)
labels      = load_labels(LABELS_PATH)
input_shape = interpreter.get_input_details()[0]["shape"]

# Título
st.title("🌿 Dashboard de Riego Inteligente")

# Sidebar: Controles
st.sidebar.header("Controles")
if st.sidebar.button("🔵 Activar Riego"):
    arduino.send_command("VALVULA ON")
    st.sidebar.success("Comando enviado: VALVULA ON")

if st.sidebar.button("🔴 Detener Riego"):
    arduino.send_command("VALVULA OFF")
    st.sidebar.success("Comando enviado: VALVULA OFF")

if st.sidebar.button("📸 Capturar y Clasificar"):
    # Captura
    ruta = capture_image(output_path="../imagenes/ultima.jpg")
    st.sidebar.write(f"Imagen capturada: {os.path.basename(ruta)}")
    # Clasificación
    img_array = preprocess_image(IMAGE_PATH, input_shape)
    output    = predict(interpreter, img_array)[0]
    etiqueta  = labels[int(pd.np.argmax(output))]
    # Guardar etiqueta en CSV (actualiza la última fila)
    df = pd.read_csv(CSV_PATH)
    df.loc[df.index[-1], "Estado visual"] = etiqueta
    df.to_csv(CSV_PATH, index=False)
    st.sidebar.success(f"Clasificación: {etiqueta}")

if st.sidebar.button("🔄 Refrescar Datos"):
    st.experimental_rerun()

# Cargo CSV
df = pd.read_csv(CSV_PATH)

# Estado actual (última fila)
ultimo = df.iloc[-1]
st.subheader("📈 Estado Actual")
st.write(f"- Fecha y Hora: **{ultimo['Fecha y Hora']}**")
st.write(f"- Humedad (raw): **{ultimo['Humedad (raw)']}**")
st.write(f"- Válvula: **{ultimo['Válvula']}**")
if "Estado visual" in df.columns:
    st.write(f"- Estado visual: **{ultimo['Estado visual']}**")

# Mostrar última imagen
st.subheader("📷 Última Imagen Capturada")
if os.path.exists(IMAGE_PATH):
    st.image(IMAGE_PATH, use_column_width=True)
else:
    st.warning("No se encontró la imagen `ultima.jpg`.")

# Mostrar historial completo
st.subheader("🗒️ Historial de Riego")
st.dataframe(df)

# Footer
st.markdown("---")
st.markdown("**Nota:** Usa los botones de la barra lateral para controlar el sistema o capturar nuevas imágenes.")

