from django.db import models


# Create your models here.
class Measurement(models.Model):
    temperature = models.PositiveSmallIntegerField()
    humidity = models.PositiveSmallIntegerField()
    light = models.PositiveSmallIntegerField()
    soil_moisture = models.PositiveSmallIntegerField()
    pump_power = models.BooleanField()
    reservoir_level = models.PositiveSmallIntegerField()
    errors = models.CharField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Measurement at {self.timestamp}"


class Warning(models.Model):
    measurement = models.ForeignKey(
        Measurement, on_delete=models.CASCADE, related_name="warnings"
    )
    message = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Warning: {self.message} at {self.timestamp}"


class ThresholdPreset(models.Model):
    moisture_threshold = models.IntegerField(default=350)
    reservoir_threshold = models.IntegerField(default=8)

    def __str__(self):
        return "Preset Thresholds"