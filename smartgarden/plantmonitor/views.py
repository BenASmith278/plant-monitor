from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now
from django.shortcuts import render, redirect
from .models import Measurement, ThresholdPreset
from datetime import timedelta
import json

manual_trigger = False  # required for pump trigger flag


def index(request):
    preset, _ = ThresholdPreset.objects.get_or_create(id=1)

    if request.method == 'POST':
        preset.moisture_threshold = int(request.POST.get('moisture_threshold'))
        preset.reservoir_threshold = int(request.POST.get('reservoir_threshold'))
        preset.save()
        return redirect('index')

    latest = Measurement.objects.order_by('-timestamp').first()

    is_connected = latest and (now() - latest.timestamp <= timedelta(seconds=30))
    presets_missing = preset.moisture_threshold is None or preset.reservoir_threshold is None

    # Define sensor info for loop rendering
    sensors = [
        {
            "id": "moisture",
            "label": "Soil Moisture",
            "value": f"{latest.soil_moisture}%" if latest else "N/A",
            "preset": f"{preset.moisture_threshold}%",
            "warning": latest and latest.soil_moisture < preset.moisture_threshold,
        },
        {
            "id": "temperature",
            "label": "Temperature",
            "value": f"{latest.temperature}°C" if latest else "N/A",
            "preset": "-",
            "warning": False
        },
        {
            "id": "humidity",
            "label": "Humidity",
            "value": f"{latest.humidity}%" if latest else "N/A",
            "preset": "-",
            "warning": False
        },
        {
            "id": "light",
            "label": "Light Level",
            "value": f"{latest.light} lx" if latest else "N/A",
            "preset": "-",
            "warning": False
        },
        {
            "id": "reservoir",
            "label": "Water Reservoir",
            "value": f"{int(latest.reservoir_level / 128 * 100)}%" if latest else "N/A",
            "preset": f"{preset.reservoir_threshold}/128",
            "warning": latest and latest.reservoir_level < preset.reservoir_threshold,
        }
    ]

    return render(request, "plantmonitor/dashboard.html", {
        "latest": latest,
        "moisture_threshold": preset.moisture_threshold,
        "reservoir_threshold": preset.reservoir_threshold,
        "is_connected": is_connected,
        "presets_missing": presets_missing,
        "sensors": sensors,
    })


@csrf_exempt
def receive_sensor_data(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            Measurement.objects.create(
                temperature=data['temperature'],
                humidity=data['humidity'],
                light=data['light'],
                soil_moisture=data['moisture'],
                pump_power=data['pump_power'],
                reservoir_level=data['res_level'],
                errors=', '.join(data['errors'])
            )
            return JsonResponse({'status': 'success'}, status=201)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'only POST allowed'}, status=405)


@csrf_exempt
def trigger_pump(request):
    global manual_trigger
    if request.method == 'POST':
        manual_trigger = True
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=405)


def poll_pump_command(request):
    global manual_trigger
    if manual_trigger:
        manual_trigger = False
        return JsonResponse({"trigger": True})
    return JsonResponse({"trigger": False})


def get_system_config(request):
    preset = ThresholdPreset.objects.first()
    return JsonResponse({
        "moisture_threshold": preset.moisture_threshold
    })


def get_chart_data(request):
    now_time = now()
    window = timedelta(minutes=3)
    cutoff = now_time - timedelta(hours=1)
    data_points = []

    measurements = Measurement.objects.filter(timestamp__gte=cutoff).order_by('timestamp')
    interval_start = None
    batch = []

    for m in measurements:
        if interval_start is None or m.timestamp > interval_start + window:
            if batch:
                data_points.append({
                    "time": interval_start.strftime("%H:%M"),
                    "soil_moisture": avg([b.soil_moisture for b in batch]),
                    "temperature": avg([b.temperature for b in batch]),
                    "humidity": avg([b.humidity for b in batch]),
                    "light": avg([b.light for b in batch]),
                    "reservoir_level": avg([b.reservoir_level for b in batch]),
                })
            interval_start = m.timestamp
            batch = [m]
        else:
            batch.append(m)

    # Final batch
    if batch:
        data_points.append({
            "time": interval_start.strftime("%H:%M"),
            "soil_moisture": avg([b.soil_moisture for b in batch]),
            "temperature": avg([b.temperature for b in batch]),
            "humidity": avg([b.humidity for b in batch]),
            "light": avg([b.light for b in batch]),
            "reservoir_level": avg([b.reservoir_level for b in batch]),
        })

    # Return consistent structure for chart.js
    return JsonResponse({
        "timestamps": [d["time"] for d in data_points],
        "soil_moisture": [d["soil_moisture"] for d in data_points],
        "temperature": [d["temperature"] for d in data_points],
        "humidity": [d["humidity"] for d in data_points],
        "light": [d["light"] for d in data_points],
        "reservoir_level": [d["reservoir_level"] for d in data_points],
    })


def avg(values):
    return round(sum(values) / len(values), 2) if values else 0