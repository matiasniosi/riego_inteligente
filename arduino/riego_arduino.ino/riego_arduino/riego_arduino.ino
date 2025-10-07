void setup() {
  Serial.begin(9600);
  pinMode(A0, INPUT);     // Sensor de humedad
  pinMode(7, OUTPUT);     // Relé (activo en bajo)
  pinMode(13, OUTPUT);    // LED indicador (activo en alto)
}

void loop() {
  int humedad = analogRead(A0);
  String estadoValvula = digitalRead(7) == LOW ? "ON" : "OFF";  // Relé activo en bajo

  // Enviar lectura
  Serial.print("Humedad:");
  Serial.print(humedad);
  Serial.print(" | Válvula: ");
  Serial.println(estadoValvula);

  // Leer comando
  if (Serial.available()) {
    String comando = Serial.readStringUntil('\n');
    comando.trim();

    if (comando == "VALVULA ON") {
      digitalWrite(7, LOW);   // Activa relé
      digitalWrite(13, HIGH); // Enciende LED
      Serial.println("✅ Comando recibido: VALVULA ON");
    } else if (comando == "VALVULA OFF") {
      digitalWrite(7, HIGH);  // Desactiva relé
      digitalWrite(13, LOW);  // Apaga LED
      Serial.println("✅ Comando recibido: VALVULA OFF");
    }
  }

  delay(10000); // Esperar 10 segundos
}
