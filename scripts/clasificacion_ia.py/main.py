#!/usr/bin/env python3
import os
import numpy as np
import pandas as pd
from datetime import datetime
from PIL import Image
import tflite_runtime.interpreter as tflite

# Ajusta estas rutas si cambias la estructura
BASE_DIR = os.path.abspath(os.path.join(__file__, "..", ".."))
MODEL_PATH = os.path.join(BASE_DIR, "modelo", "modelo.tflite")
LABELS_PATH = os.path.join(BASE_DIR, "modelo", "labels.txt")
IMAGE_PATH  = os.path.join(BASE_DIR, "imagenes", "ultima.jpg")
CSV_PATH    = os.path.join(BASE_DIR, "datos", "historial_riego.csv")

def load_model(model_path: str):
    interpreter = tflite.Interpreter(model_path=model_path)
    interpreter.allocate_tensors()
    return interpreter

def load_labels(labels_path: str) -> list:
    with open(labels_path, "r") as f:
        return [line.strip() for line in f.readlines()]

def preprocess_image(image_path: str, input_shape: tuple) -> np.ndarray:
    img = Image.open(image_path).convert("RGB")
    img = img.resize((input_shape[1], input_shape[2]))
    arr = np.asarray(img, dtype=np.float32) / 255.0
    return np.expand_dims(arr, axis=0)

def predict(interpreter, input_data: np.ndarray) -> np.ndarray:
    input_index  = interpreter.get_input_details()[0]["index"]
    output_index = interpreter.get_output_details()[0]["index"]
    interpreter.set_tensor(input_index, input_data)
    interpreter.invoke()
    return interpreter.get_tensor(output_index)

def append_visual_to_csv(timestamp: str, label: str):
    df = pd.read_csv(CSV_PATH)
    df["Estado visual"] = df.get("Estado visual", "")
    df.loc[len(df) - 1, "Estado visual"] = label
    df.to_csv(CSV_PATH, index=False)

def main():
    # Cargar modelo y etiquetas
    interpreter = load_model(MODEL_PATH)
    labels      = load_labels(LABELS_PATH)
    
    # Obtener forma de entrada (batch, height, width, channels)
    input_details = interpreter.get_input_details()[0]
    input_shape   = input_details["shape"]
    
    # Preprocesar imagen
    input_data = preprocess_image(IMAGE_PATH, input_shape)
    
    # Inferencia
    output = predict(interpreter, input_data)[0]
    predicted_label = labels[np.argmax(output)]
    score = float(np.max(output))
    
    # Registro por consola
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] Predicción visual: {predicted_label} ({score:.2f})")
    
    # Guardar etiqueta en el CSV, junto al último registro
    append_visual_to_csv(timestamp, predicted_label)

if __name__ == "__main__":
    main()
