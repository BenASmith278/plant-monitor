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
