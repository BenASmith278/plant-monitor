import serial
import json
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout


class SmartGardenUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        try:
            self.arduino = serial.Serial("/dev/ttyACM0", 9600, timeout=1)
        except Exception as e:
            print(f"Failed to connect to Arduino: {e}")
            self.arduino = None
        self.pump_on = False
        Clock.schedule_interval(self.read_data, 2)

    def toggle_power(self, instance):
        if not self.arduino:
            return
        command = b"1\n" if not self.pump_on else b"0\n"
        self.arduino.write(command)
        self.pump_on = not self.pump_on

    def read_data(self, dt):
        if not self.arduino:
            return
        try:
            line = self.arduino.readline().decode("utf-8").strip()
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
        return PlantMonitorUI()


if __name__ == "__main__":
    PlantMonitorUI().run()
