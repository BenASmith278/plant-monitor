
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.views.generic import ListView, DetailView
from django.utils.timezone import now
from .models import Measurement, Warning
from datetime import timedelta

from django.shortcuts import render, redirect

from .models import Measurement, ThresholdPreset

def index(request):
    # Get or create the single preset instance
    preset, _ = ThresholdPreset.objects.get_or_create(id=1)

    # Handle POST (form submission)
    if request.method == 'POST':
        preset.moisture_threshold = int(request.POST.get('moisture_threshold'))
        preset.reservoir_threshold = int(request.POST.get('reservoir_threshold'))
        preset.save()
        return redirect('index')

    latest = Measurement.objects.order_by('-timestamp').first()

    is_connected = latest and (now() - latest.timestamp <= timedelta(seconds=30))
    presets_missing = preset.moisture_threshold is None or preset.reservoir_threshold is None

    context = {
        "latest": latest,
        "moisture_threshold": preset.moisture_threshold,
        "reservoir_threshold": preset.reservoir_threshold,
        "is_connected": is_connected,
        "presets_missing": presets_missing,
    }
    return render(request, "plantmonitor/dashboard.html", context)


# class DetailView(DetailView):
#     model = Measurement
#     template_name = 'measurement_detail.html'
#     context_object_name = 'measurement'

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['warnings'] = Warning.objects.filter(measurement=self.object)
#         return context


def get_system_config(request):
    preset = ThresholdPreset.objects.first()
    return JsonResponse({
        "moisture_threshold": preset.moisture_threshold
    })
    
def poll_pump_command(request):
    global manual_trigger
    if manual_trigger:
        manual_trigger = False
        return JsonResponse({"trigger": True})
    return JsonResponse({"trigger": False})

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
                errors=', '.join(data['errors'])  # joining the error list as a string
            )
            return JsonResponse({'status': 'success'}, status=201)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    else:
        return JsonResponse({'status': 'only POST allowed'}, status=405)
    
@csrf_exempt
def trigger_pump(request):
    global manual_trigger
    if request.method == 'POST':
        manual_trigger = True
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=405)