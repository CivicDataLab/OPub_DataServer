from django.db import models


class Geography(models.Model):
    name = models.CharField(max_length=75, unique=True)
