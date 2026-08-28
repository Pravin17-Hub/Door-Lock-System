/*
  ===================================================================
  FaceSecure - ESP32 Servo Motor & Door Lock Hardware Controller
  ===================================================================
  
  Hardware Wiring Setup:
  -------------------------------------------------------------------
  Component            Wire Color     ESP32 Pin Label
  -------------------------------------------------------------------
  Servo Signal Wire    Yellow/Orange  GPIO 18 (Labeled D18 or 18)
  Servo Power Wire     Red            5V or VIN pin (5V Power)
  Servo Ground Wire    Black/Brown    GND pin
  Buzzer Positive (+)  Red / Any      GPIO 19 (Labeled D19 or 19)
  Buzzer Ground (-)    Black          GND pin
  ===================================================================
*/

#include <ESP32Servo.h>

Servo doorServo;

// Pin Definitions
const int SERVO_PIN = 18;   // Servo signal pin on GPIO 18
const int BUZZER_PIN = 19;  // Buzzer alarm pin on GPIO 19
const int GREEN_LED = 21;   // Access Granted LED on GPIO 21
const int RED_LED = 22;     // Access Denied LED on GPIO 22

// Servo Angle Settings
const int SERVO_LOCKED_POS = 0;    // Door Closed (0 degrees)
const int SERVO_UNLOCKED_POS = 90; // Door Opened (90 degrees)

void setup() {
  // Initialize Serial Communication at 9600 Baud
  Serial.begin(9600);
  
  // Set 50Hz PWM frequency and pulse width bounds (500us to 2400us) for smooth rotation
  doorServo.setPeriodHertz(50);
  doorServo.attach(SERVO_PIN, 500, 2400);
  
  // Initialize Servo to Locked Position (0 degrees)
  doorServo.write(SERVO_LOCKED_POS);
  delay(500);

  // Set Pin Modes
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(GREEN_LED, OUTPUT);
  pinMode(RED_LED, OUTPUT);

  digitalWrite(GREEN_LED, LOW);
  digitalWrite(RED_LED, LOW);
  digitalWrite(BUZZER_PIN, LOW);

  Serial.println("FACESECURE_ESP32_READY");
}

void loop() {
  // Listen for USB Serial Commands from Flask Web Server
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    command.toUpperCase();

    if (command == "UNLOCK") {
      // Rotate 90 degrees (Open Door)
      digitalWrite(GREEN_LED, HIGH);
      digitalWrite(RED_LED, LOW);
      
      doorServo.write(SERVO_UNLOCKED_POS);
      delay(600); // Allow motor time to sweep smoothly to 90 degrees
      
      // Short authorization beep
      tone(BUZZER_PIN, 1000, 150);
      Serial.println("STATUS:UNLOCKED");
    } 
    else if (command == "LOCK") {
      // Rotate back to 0 degrees (Close Door)
      doorServo.write(SERVO_LOCKED_POS);
      delay(600); // Allow motor time to return smoothly to 0 degrees
      
      digitalWrite(GREEN_LED, LOW);
      digitalWrite(RED_LED, LOW);
      digitalWrite(BUZZER_PIN, LOW);
      Serial.println("STATUS:LOCKED");
    } 
    else if (command == "ALARM") {
      // Access Denied Warning Alarm
      digitalWrite(RED_LED, HIGH);
      digitalWrite(GREEN_LED, LOW);
      
      for (int i = 0; i < 3; i++) {
        tone(BUZZER_PIN, 2000, 100);
        delay(150);
      }
      digitalWrite(RED_LED, LOW);
      Serial.println("STATUS:ALARM_TRIGGERED");
    }
  }
}
