#!/usr/bin/env python3
import os
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from scripts.comunicacion_serial import ArduinoSerial
from scripts.captura_imagen import capture_image
from scripts.clasificacion_ia import (
    load_model,
    load_labels,
    preprocess_image,
    predict,
)

# Configuración de logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Rutas base
BASE_DIR    = os.path.abspath(os.path.join(__file__, "..", ".."))
IMAGE_PATH  = os.path.join(BASE_DIR, "imagenes", "ultima.jpg")
MODEL_PATH  = os.path.join(BASE_DIR, "modelo", "modelo.tflite")
LABELS_PATH = os.path.join(BASE_DIR, "modelo", "labels.txt")

# Instancias globales
arduino     = ArduinoSerial()
interpreter = load_model(MODEL_PATH)
labels      = load_labels(LABELS_PATH)
input_shape = interpreter.get_input_details()[0]["shape"]

def start(update: Update, context: CallbackContext) -> None:
    text = (
        "🤖 ¡Bienvenido al Sistema de Riego Inteligente!\n\n"
        "Comandos disponibles:\n"
        "/estado     — Muestra humedad y estado de la válvula\n"
        "/activar    — Abre la válvula (ON)\n"
        "/desactivar — Cierra la válvula (OFF)\n"
        "/foto       — Envía la última imagen capturada\n"
        "/clasificar — Captura una nueva foto, la clasifica y actualiza el historial\n"
    )
    update.message.reply_text(text)

def estado(update: Update, context: CallbackContext) -> None:
    try:
        last = arduino.get_last_record()
        if not last:
            update.message.reply_text("⚠️ No hay datos registrados aún.")
            return

        msg = (
            f"📊 Estado actual:\n"
            f"- Fecha y Hora: {last['Fecha y Hora']}\n"
            f"- Humedad (raw): {last['Humedad (raw)']}\n"
            f"- Válvula: {last['Válvula']}\n"
        )
        if last.get("Estado visual"):
            msg += f"- Estado visual: {last['Estado visual']}\n"
        if last.get("Observaciones"):
            msg += f"- Observaciones: {last['Observaciones']}\n"

        update.message.reply_text(msg)

        if os.path.exists(IMAGE_PATH):
            with open(IMAGE_PATH, "rb") as img:
                update.message.reply_photo(photo=img)
    except Exception as e:
        logger.error(f"Error en /estado: {e}")
        update.message.reply_text("⚠️ No pude leer el historial de riego.")

def activar(update: Update, context: CallbackContext) -> None:
    arduino.send_command("VALVULA ON")
    update.message.reply_text("🔵 Válvula ACTIVADA.")

def desactivar(update: Update, context: CallbackContext) -> None:
    arduino.send_command("VALVULA OFF")
    update.message.reply_text("🔴 Válvula DESACTIVADA.")

def foto(update: Update, context: CallbackContext) -> None:
    if os.path.exists(IMAGE_PATH):
        with open(IMAGE_PATH, "rb") as img:
            update.message.reply_photo(photo=img)
    else:
        update.message.reply_text("⚠️ No hay ninguna imagen disponible.")

def clasificar(update: Update, context: CallbackContext) -> None:
    try:
        ruta = capture_image(output_path=IMAGE_PATH)
        arr  = preprocess_image(IMAGE_PATH, input_shape)
        out  = predict(interpreter, arr)[0]
        label = labels[int(out.argmax())]

        import pandas as pd
        df = pd.read_csv(arduino.csv_path)
        if not df.empty:
            df.loc[df.index[-1], "Estado visual"] = label
            df.to_csv(arduino.csv_path, index=False)

        update.message.reply_text(f"📸 Imagen capturada y clasificada como *{label}*.", parse_mode="Markdown")
        with open(IMAGE_PATH, "rb") as img:
            update.message.reply_photo(photo=img)
    except Exception as e:
        logger.error(f"Error en /clasificar: {e}")
        update.message.reply_text("⚠️ Ocurrió un error al capturar o clasificar la imagen.")

def main() -> None:
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        logger.error("Debes exportar la variable TELEGRAM_TOKEN con el token de tu bot.")
        return

    updater = Updater(token=token, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("estado", estado))
    dp.add_handler(CommandHandler("activar", activar))
    dp.add_handler(CommandHandler("desactivar", desactivar))
    dp.add_handler(CommandHandler("foto", foto))
    dp.add_handler(CommandHandler("clasificar", clasificar))

    updater.start_polling()
    logger.info("Bot de Telegram iniciado. Esperando comandos...")
    updater.idle()

if __name__ == "__main__":
    main()
