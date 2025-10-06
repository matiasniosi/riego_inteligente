# scripts/telegram_bot.py

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
CSV_PATH    = os.path.join(BASE_DIR, "datos", "historial_riego.csv")

# Instancias globales
arduino     = ArduinoSerial()
interpreter = load_model(MODEL_PATH)
labels      = load_labels(LABELS_PATH)
input_shape = interpreter.get_input_details()[0]["shape"]


def start(update: Update, context: CallbackContext) -> None:
    """Mensaje de bienvenida y lista de comandos."""
    text = (
        "🤖 ¡Bienvenido al Sistema de Riego Inteligente!\n\n"
        "Comandos disponibles:\n"
        "/estado     — Muestra humedad y estado de la válvula\n"
        "/activar    — Abre la válvula (ON)\n"
        "/desactivar — Cierra la válvula (OFF)\n"
        "/foto       — Envia la última imagen capturada\n"
        "/clasificar — Captura una nueva foto, la clasifica y actualiza el historial\n"
    )
    update.message.reply_text(text)


def estado(update: Update, context: CallbackContext) -> None:
    """Envía la última lectura de humedad, estado de válvula y etiqueta visual."""
    try:
        # Leer último registro
        import pandas as pd
        df    = pd.read_csv(CSV_PATH)
        last  = df.iloc[-1]
        msg   = (
            f"📊 Estado actual:\n"
            f"- Fecha y Hora: {last['Fecha y Hora']}\n"
            f"- Humedad (raw): {last['Humedad (raw)']}\n"
            f"- Válvula: {last['Válvula']}\n"
        )
        if "Estado visual" in last:
            msg += f"- Estado visual: {last['Estado visual']}\n"
        update.message.reply_text(msg)
    except Exception as e:
        logger.error(f"Error en /estado: {e}")
        update.message.reply_text("⚠️ No pude leer el historial de riego.")


def activar(update: Update, context: CallbackContext) -> None:
    """Abre la válvula."""
    arduino.send_command("VALVULA ON")
    update.message.reply_text("🔵 Válvula ACTIVADA.")


def desactivar(update: Update, context: CallbackContext) -> None:
    """Cierra la válvula."""
    arduino.send_command("VALVULA OFF")
    update.message.reply_text("🔴 Válvula DESACTIVADA.")


def foto(update: Update, context: CallbackContext) -> None:
    """Envía la última imagen al usuario."""
    if os.path.exists(IMAGE_PATH):
        with open(IMAGE_PATH, "rb") as img:
            update.message.reply_photo(photo=img)
    else:
        update.message.reply_text("⚠️ No hay ninguna imagen disponible.")


def clasificar(update: Update, context: CallbackContext) -> None:
    """Captura una foto, la clasifica con TensorFlow Lite y actualiza el historial."""
    try:
        # Capturar nueva imagen
        ruta = capture_image(output_path="../imagenes/ultima.jpg")
        # Preprocesar y predecir
        arr  = preprocess_image(IMAGE_PATH, input_shape)
        out  = predict(interpreter, arr)[0]
        label = labels[int(out.argmax())]

        # Actualizar CSV (última fila)
        import pandas as pd
        df = pd.read_csv(CSV_PATH)
        df.loc[df.index[-1], "Estado visual"] = label
        df.to_csv(CSV_PATH, index=False)

        # Responder al usuario
        update.message.reply_text(f"📸 Imagen capturada y clasificada como *{label}*.", parse_mode="Markdown")
        with open(IMAGE_PATH, "rb") as img:
            update.message.reply_photo(photo=img)
    except Exception as e:
        logger.error(f"Error en /clasificar: {e}")
        update.message.reply_text("⚠️ Ocurrió un error al capturar o clasificar la imagen.")


def main() -> None:
    """Inicializa el bot y registra los handlers."""
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        logger.error("Debes exportar la variable TELEGRAM_TOKEN con el token de tu bot.")
        return

    updater = Updater(token=token, use_context=True)
    dp = updater.dispatcher

    # Registramos comandos
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("estado", estado))
    dp.add_handler(CommandHandler("activar", activar))
    dp.add_handler(CommandHandler("desactivar", desactivar))
    dp.add_handler(CommandHandler("foto", foto))
    dp.add_handler(CommandHandler("clasificar", clasificar))

    # Iniciar polling
    updater.start_polling()
    logger.info("Bot de Telegram iniciado. Esperando comandos...")
    updater.idle()


if __name__ == "__main__":
    main()
