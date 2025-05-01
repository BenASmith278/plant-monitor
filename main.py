import serial
import json
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty
from kivy.lang import Builder
from time import time

MOISTURE_THRESHOLD = 200


class SmartGardenUI(BoxLayout):
    pump_button_text = StringProperty("Turn Pump ON")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.arduino = None
        self.last_data = {}
        self.last_successful_read = 0  

        self.connect_arduino()
        Clock.schedule_interval(self.check_connection, 10)
        Clock.schedule_interval(self.read_data, 2)

    def connect_arduino(self):
        try:
            self.arduino = serial.Serial("/dev/ttyACM1", 9600, timeout=1)
            self.ids.connection_status.text = "Connected to Arduino"
            self.ids.connection_status.color = (0.2, 0.6, 0.2, 1)
        except Exception as e:
            self.arduino = None
            self.show_connection_error()

    def check_connection(self, dt):
        if time() - self.last_successful_read > 10:
            self.show_connection_error()
        else:
            self.ids.connection_status.text = "Connected to Arduino"
            self.ids.connection_status.color = (0.2, 0.6, 0.2, 1)

    def show_connection_error(self):
        self.ids.connection_status.text = "Waiting to connect to Arduino"
        self.ids.connection_status.color = (1, 0, 0, 1)

    def toggle_power(self, instance):
        if not self.arduino:
            return
        try:
            self.arduino.write(b"manual_water\n")
        except Exception as e:
            self.show_connection_error()

    def read_data(self, dt):
        if not self.arduino:
            self.display_last_known_data()
            return

        try:
            line = self.arduino.readline().decode("utf-8").strip()
            line = line.replace("'", '"')
            if line:
                data = json.loads(line)
                self.last_data = data
                self.last_successful_read = time()  

                moisture = data.get('moisture', 'N/A')
                reservoir = data.get('res_level', 'N/A')

                self.ids.moisture.text = str(moisture)
                self.ids.reservoir.text = str(reservoir)

                if isinstance(moisture, int) or str(moisture).isdigit():
                    if int(moisture) < MOISTURE_THRESHOLD:
                        self.ids.status_message.text = "Plant is not happy"
                        self.ids.status_message.color = (1, 0.4, 0.4, 1)
                    else:
                        self.ids.status_message.text = "Plant is happy"
                        self.ids.status_message.color = (0.2, 0.6, 0.2, 1)
        except Exception as e:
            self.show_connection_error()
            self.display_last_known_data()

    def display_last_known_data(self):
        if self.last_data:
            self.ids.moisture.text = str(self.last_data.get('moisture', 'N/A'))
            self.ids.reservoir.text = str(self.last_data.get('res_level', 'N/A'))
            self.ids.status_message.text = "Showing last known values"
            self.ids.status_message.color = (0.6, 0.6, 0.6, 1)

class PlantMonitorUI(App):
    def build(self):
        return SmartGardenUI()

if __name__ == "__main__":
    PlantMonitorUI().run()