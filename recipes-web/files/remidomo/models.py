from django.db import models


class Mesure(models.Model):
    name = models.CharField(max_length=64)
    address = models.CharField(max_length=16)
    timestamp = models.DateTimeField()
    value = models.FloatField()
    units = models.CharField(max_length=8)
    type = models.CharField(max_length=10)
