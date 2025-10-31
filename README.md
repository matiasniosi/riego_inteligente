El Cerebro del Riego: El Firmware (riego_arduino)
Este directorio contiene el sketch riego_arduino.ino, que es el firmware que se carga en el microcontrolador Arduino Uno.

Este código actúa como el "esclavo" del sistema. Su única responsabilidad es manejar el hardware de bajo nivel (sensores y relés) y comunicarse con el "maestro" (la Raspberry Pi) a través del puerto USB (Serial).

💡 Características Principales
Modular y Escalable: Diseñado para manejar múltiples sensores y relés con solo cambiar dos constantes (NUM_SENSORES y NUM_RELES).

Riego Inteligente (Histéresis): Utiliza dos umbrales (umbralSeco y umbralHumedo) para evitar que la válvula se encienda y apague constantemente si la humedad está fluctuando en un solo punto.

Control Dual:

Modo Automático: El Arduino decide por sí mismo cuándo regar basándose en los umbrales.

Modo Manual: La Raspberry Pi puede anular la lógica automática y forzar el encendido (VALVULA 0 ON) o apagado (VALVULA 0 OFF) de cualquier válvula en cualquier momento.

🔌 Configuración Plug and Play
Para adaptar este código a tu propio montaje, solo necesitas ajustar 3 secciones al inicio del archivo riego_arduino.ino:

1. CONFIGURACIÓN GENERAL:

#define NUM_SENSORES 1: Cambia este 1 por el número de sensores que tengas.

#define NUM_RELES 1: Cambia este 1 por el número de relés/válvulas que tengas.

2. DEFINICIÓN DE PINES:

const int pinesHumedad[] = {A0};: Añade los pines analógicos de tus sensores (ej: {A0, A1, A2}).

const int pinesRele[] = {7};: Añade los pines digitales de tus relés (ej: {7, 8, 9}).

4. UMBRALES DE RIEGO (AJUSTABLES):

int umbralSeco = 800;: ¡El más importante! Este es el valor del sensor (0-1023) que se considera "seco". El riego se activará por encima de este valor.

int umbralHumedo = 600;: Este es el valor que se considera "húmedo". El riego se desactivará por debajo de este valor.

⚠️ ¡Calibra tus sensores! El valor 800 (seco) y 600 (húmedo) son ejemplos. Tus sensores pueden tener valores diferentes. Mide el valor del sensor al aire (seco) y en un vaso de agua (húmedo) para encontrar tus propios umbrales.

📡 Protocolo de Comunicación Serial (Baud: 9600)
Para que la Raspberry Pi pueda entender al Arduino (y viceversa), se usa un protocolo de texto simple a través del puerto serial (USB).

1. Arduino → Raspberry Pi (Envío de datos)
El Arduino envía el estado de todos sus sensores y relés cada segundo, línea por línea. El formato es:

DATA,[indice],[humedad],[estado_rele]

indice: El número del sensor/relé (empezando en 0).

humedad: El valor crudo del sensor de humedad (ej: 785).

estado_rele: 1 si el relé está ON (regando), 0 si está OFF.

Ejemplo de salida (para 2 sensores):

DATA,0,810,0
DATA,1,550,1
Traducción: El sensor 0 está seco (810) y su válvula está apagada (0). El sensor 1 está húmedo (550) y su válvula está encendida (1).

2. Raspberry Pi → Arduino (Envío de comandos)
La Raspberry Pi puede enviar comandos manuales al Arduino en cualquier momento. El formato es:

VALVULA [indice] [ON/OFF]

Ejemplos de comandos:

VALVULA 0 ON: Fuerza el encendido del relé/válvula 0.

VALVULA 0 OFF: Fuerza el apagado del relé/válvula 0.

VALVULA 1 ON: Fuerza el encendido del relé/válvula 1.
