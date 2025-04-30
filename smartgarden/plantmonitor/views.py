
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Measurement
from django.shortcuts import render
from django.views.generic import ListView, DetailView

from .models import Measurement, Warning


# Create your views here.
def index(request):
    context = {}
    return render(request, "plantmonitor/dashboard.html", context)


# class DetailView(DetailView):
#     model = Measurement
#     template_name = 'measurement_detail.html'
#     context_object_name = 'measurement'

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['warnings'] = Warning.objects.filter(measurement=self.object)
#         return context



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