from django.db import models


class Sector(models.Model):
    name = models.CharField(max_length=75)
