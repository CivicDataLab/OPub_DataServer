from django.db import models


class Geography(models.Model):
    name = models.CharField(max_length=75, unique=True)
    official_id = models.CharField(max_length=100, null=True, blank=True, unique=False, default='')
