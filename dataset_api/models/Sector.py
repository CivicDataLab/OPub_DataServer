from django.db import models
from django.contrib.postgres.fields import ArrayField


class Sector(models.Model):
    name = models.CharField(max_length=75)
    description = models.CharField(max_length=100, null=False)
    highlights = ArrayField(models.CharField(max_length=100, blank=True, null=True), blank=True, null=True)