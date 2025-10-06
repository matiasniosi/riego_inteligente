int sensorPin = A0;
int relePin = 8;
String comando = "";

void setup() {
  Serial.begin(9600);
  pinMode(relePin, OUTPUT);
  digitalWrite(relePin, LOW); // válvula apagada
}

void loop() {
  int humedad = analogRead(sensorPin);
  String estadoValvula = digitalRead(relePin) == HIGH ? "ON" : "OFF";

  // Enviar datos cada 10 segundos
  Serial.println("Humedad: " + String(humedad) + " | Válvula: " + estadoValvula);
  delay(10000);

  // Leer comando desde Raspberry
  if (Serial.available()) {
    comando = Serial.readStringUntil('\n');
    comando.trim();

    if (comando == "VALVULA ON") {
      digitalWrite(relePin, HIGH);
    } else if (comando == "VALVULA OFF") {
      digitalWrite(relePin, LOW);
    }
  }
}
