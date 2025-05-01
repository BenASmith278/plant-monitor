from django.urls import path
from . import views

urlpatterns = [
    path("api/sensor-data/", views.receive_sensor_data, name="receive_sensor_data"),
    path("api/system-config/", views.get_system_config, name="get_system_config"),
    path("api/trigger-pump/", views.trigger_pump, name="trigger_pump"),
    path("api/poll-pump/", views.poll_pump_command, name="poll_pump"),
    path("", views.index, name="index"),
]