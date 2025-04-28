#include "Adafruit_seesaw.h"
#include <Wire.h>
#include <DHT11.h>

// pin numbers and constants
#define photoResPin A0
#define resSensorPin A1
#define resSensorPower 4
#define pumpPowerPin 3
#define DHTPin 2
#define twoSeconds 2000

// global vars
Adafruit_seesaw soilSensor;
DHT11 dht11(DHTPin);
int temperature;
int humidity;
int lightLevel;
int resLevel;
int moisture;
bool pumpPower = false;
String lastError = "None";
String error = "None";
unsigned long lastWatering = millis();

// thresholds
int moistureThreshold = 400;
unsigned long wateringInterval = 20000; // default 20s

void setup() {
  Serial.begin(9600);
  pinMode(resSensorPower, OUTPUT);
  pinMode(pumpPowerPin, OUTPUT);

  if (!soilSensor.begin(0x36)) {
    setError("Soil moisture sensor not found! Check connections and restart.");
    // set moisture to moisture threshold to avoid constant watering
    moisture = moistureThreshold;
  }
}

void loop() {
  // stop pump at start of every loop to avoid runaway
  stopPump();
  // clear errors so only recent ones show
  error = "None";
  lastError = "None";

  unsigned long startTime = millis();

  readDHT11(temperature, humidity);
  readSoilSensor(moisture);
  readLightLevel(lightLevel);
  readResevoirLevel(resLevel);

  if (moisture < moistureThreshold) {
    // if watering interval has elapsed
    if ((millis() - lastWatering) > wateringInterval) {
      startPump();
    }
  }

  // print out to pi
  // no need for JSON library
  Serial.print("{\"moisture\":");
  Serial.print(moisture);
  Serial.print(", \"light\":");
  Serial.print(lightLevel);
  Serial.print(", \"res_level\":");
  Serial.print(resLevel);
  Serial.print(", \"temperature\":");
  Serial.print(temperature);
  Serial.print(", \"humidity\":");
  Serial.print(humidity);
  Serial.print(", \"pump_power\":");
  Serial.print(pumpPower);
  Serial.print(", \"errors\": [\"");
  Serial.print(error);
  Serial.print("\",\"");
  Serial.print(lastError);
  Serial.print("\"]");
  Serial.println("}");
  
  // adjust for reading time so readings happen on a consistent interval
  unsigned long endTime = millis();
  unsigned long duration = endTime - startTime;
  delay(twoSeconds - duration);
}

void readDHT11(int &temperature, int &humidity) {
  int tempSum = 0, humSum = 0, result = 0;

  for (int i = 0; i < 3; i++) {
    int thisTemp, thisHum;
    result += dht11.readTemperatureHumidity(thisTemp, thisHum);
    tempSum += thisTemp;
    humSum += thisHum;
  }

  if (result != 0) {
    setError(DHT11::getErrorString(result));
  } else {
    // average the three readings
    // only update temperature and humidity if all valid
    temperature = tempSum / 3;
    humidity = humSum / 3;
  }
}

void readSoilSensor(int &moisture) {
  int readings = 0;
  for (int i = 0; i < 3; i++) {
    readings += soilSensor.touchRead(0);
  }
  
  moisture = readings / 3;
}

void readLightLevel(int &light) {
  int readings = 0;
  for (int i = 0; i < 3; i++) {
    readings += analogRead(photoResPin);
  }

  light = readings / 3;
}

void readResevoirLevel(int &level) {
  int readings = 0;

  // only power sensor for reading time to reduce corrosion
  digitalWrite(resSensorPower, HIGH);
  delay(10);

  for (int i = 0; i < 3; i++) {
    readings += analogRead(resSensorPin);
  }

  digitalWrite(resSensorPower, LOW);
  level = readings / 3;
}

void startPump() {
  pumpPower = true;
  lastWatering = millis();
  digitalWrite(pumpPowerPin, HIGH);
}

void stopPump() {
  pumpPower = false;
  digitalWrite(pumpPowerPin, LOW);
}

void setError(String newError) {
  lastError = error;
  error = newError;
}