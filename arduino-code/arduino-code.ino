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
int moistureAverage = 512;
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
    // make this error persist on the front end
    setError("Soil moisture sensor not found! Check connections and restart.");
    // set moisture to moisture threshold to avoid constant watering
    moisture = moistureThreshold;
  }
}

void loop() {
  unsigned long startTime = millis();

  // stop pump at start of every loop to avoid runaway
  stopPump();

  // calculate moving average of last 10 moisture readings to avoid watering while water is propogating
  moistureAverage = (moistureAverage * 9 + moisture) / 10;
  if (moisture < moistureThreshold && abs(moisture - moistureAverage) < 10) {
    // if watering interval has elapsed
    if ((millis() - lastWatering) > wateringInterval) {
      startPump();
    }
  }

  // check for incoming message
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    if (command == "manual_water") {
      startPump();
    } else if (command.startsWith("threshold:")) {
      moistureThreshold = command.substring(10).toInt();
    }
  }
  
  // clear errors so only recent ones show
  error = "None";
  lastError = "None";

  readDHT11(temperature, humidity);
  readSoilSensor(moisture);
  readLightLevel(lightLevel);
  readResevoirLevel(resLevel);

  printToSerial();
  
  // adjust for reading time so readings happen on a consistent interval
  unsigned long endTime = millis();
  unsigned long duration = endTime - startTime;
  delay(twoSeconds - duration);
}

void printToSerial() {
  // print out to pi
  // no need for JSON library but it might make this easier to read
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
    // dont check expected range since the library deals with errors
    temperature = tempSum / 3;
    humidity = humSum / 3;
  }
}

void readSoilSensor(int &moisture) {
  int readings = 0;
  for (int i = 0; i < 3; i++) {
    readings += soilSensor.touchRead(0);
  }
  
  readings /= 3;
  // check that measurement is in expected range
  if (readings < 0 || readings > 1024) {
    return;
  }
  moisture = readings;
}

void readLightLevel(int &light) {
  int readings = 0;
  for (int i = 0; i < 3; i++) {
    readings += analogRead(photoResPin);
  }

  readings /= 3;
  // check that measurement is in expected range
  if (readings < 0 || readings > 1024) {
    return;
  }
  light = readings;
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
  
  readings /= 3;
  // check that the measurement is in the expected range
  if (readings < 0 || readings > 128) {
    return;
  }
  level = readings;
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