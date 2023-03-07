from django.db import models
from django.contrib.postgres.fields import ArrayField


class Sector(models.Model):
    name = models.CharField(max_length=75)
    description = models.CharField(max_length=1000, null=False)
    highlights = ArrayField(models.CharField(max_length=100, blank=True, null=True), blank=True, null=True)
    official_id = models.CharField(max_length=100, null=True, unique=False, default='')
    parent_id = models.ForeignKey('self', null=True, blank=True, default='')