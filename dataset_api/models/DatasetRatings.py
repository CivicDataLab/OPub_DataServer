from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from .Dataset import Dataset
from ..enums import RatingStatus


class DatasetRatings(models.Model):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    review = models.CharField(max_length=500)
    # overall = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(5.0)])
    data_quality = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)]
    )
    status = models.CharField(max_length=50, choices=RatingStatus.choices)
    user = models.CharField(max_length=50, blank=False, null=False)
    modified = models.DateTimeField(auto_now=True)
    issued = models.DateTimeField(auto_now_add=True)
    # data_standards = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(5.0)])
    # coverage = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(5.0)])
