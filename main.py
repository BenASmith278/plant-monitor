import serial
import json
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty


class SmartGardenUI(BoxLayout):
    pump_button_text = StringProperty("Turn Pump ON")  # Initially OFF

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.arduino = None
        self.pump_on = False

        try:
            self.arduino = serial.Serial("/dev/ttyACM0", 9600, timeout=1)
        except Exception as e:
            print(f"Failed to connect to Arduino: {e}")
            Clock.schedule_once(lambda dt: self.show_connection_error(), 0)

        Clock.schedule_interval(self.read_data, 2)

    def show_connection_error(self):
        try:
            self.ids.connection_status.text = "Not connected to Arduino"
        except Exception as e:
            print(f"UI not ready to show connection error: {e}")

    def toggle_power(self, instance):
        if not self.arduino:
            return
        command = b"1\n" if not self.pump_on else b"0\n"
        self.arduino.write(command)
        self.pump_on = not self.pump_on
        self.pump_button_text = "Turn Pump OFF" if self.pump_on else "Turn Pump ON"

    def read_data(self, dt):
        if not self.arduino:
            return
        try:
            line = self.arduino.readline().decode("utf-8").strip()
            line = line.replace("'", '"')
            print(line)

            if line:
                data = json.loads(line)
                self.ids.moisture.text = f"Moisture: {data.get('moisture', 'N/A')}"
                self.ids.temp.text = f"Temperature: {data.get('temperature', 'N/A')} °C"
                self.ids.hum.text = f"Humidity: {data.get('humidity', 'N/A')} %"
                self.ids.light.text = f"Light: {data.get('light', 'N/A')}"
                self.ids.pump_status.text = (
                    "Pump: ON" if data.get("pump_power") else "Pump: OFF"
                )
                self.ids.connection_status.text = (
                    f"Reservoir: {data.get('res_level', 'N/A')}%"
                )
        except Exception as e:
            self.ids.connection_status.text = f"Error reading data: {e}"


class PlantMonitorUI(App):
    def build(self):
        return SmartGardenUI()


if __name__ == "__main__":
    PlantMonitorUI().run()
