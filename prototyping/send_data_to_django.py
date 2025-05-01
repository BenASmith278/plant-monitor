import serial
import requests
import json
import time

# === CONFIGURATION ===
SERIAL_PORT = '/dev/ttyACM0'
BAUD_RATE = 9600

DJANGO_BASE_URL = 'http://172.20.8.32:8000'
SENSOR_API = f'{DJANGO_BASE_URL}/api/sensor-data/'
CONFIG_API = f'{DJANGO_BASE_URL}/api/system-config/'
POLL_API = f'{DJANGO_BASE_URL}/api/poll-pump/'

# === MAIN LOGIC ===
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)
    print("Connected to Arduino.")

    # Send initial threshold to Arduino
    try:
        config = requests.get(CONFIG_API).json()
        threshold = config.get("moisture_threshold", 350)
        ser.write(f"threshold:{threshold}\n".encode("utf-8"))
        print(f"Sent threshold to Arduino: {threshold}")
    except Exception as e:
        print("Failed to send threshold:", e)

    while True:
        try:
            # Read data from Arduino
            line = ser.readline().decode('utf-8').strip()
            if line:
                print(f"Received from Arduino: {line}")
                try:
                    data = json.loads(line)
                    response = requests.post(SENSOR_API, json=data)
                    print(f"Sent to Django. Status: {response.status_code} | Response: {response.text}")
                except json.JSONDecodeError:
                    print("Invalid JSON from Arduino:", line)

            # Poll Django to check for manual pump trigger
            try:
                pump_cmd = requests.get(POLL_API).json()
                if pump_cmd.get("trigger"):
                    ser.write(b"manual_water\n")
                    print("Sent manual pump command to Arduino.")
            except Exception as e:
                print("Failed to check pump command:", e)

            time.sleep(5)

        except requests.exceptions.RequestException as e:
            print("Failed to send data:", e)

except serial.SerialException as e:
    print("Could not open serial port:", e)
