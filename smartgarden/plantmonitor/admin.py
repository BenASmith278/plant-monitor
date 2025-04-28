from django.contrib import admin

from .models import Measurement, Warning

# Register your models here.
admin.site.register(Measurement)
admin.site.register(Warning)
