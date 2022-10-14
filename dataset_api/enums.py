from enum import Enum
from django.db import models


class RatingStatus(models.TextChoices):
    CREATED = "CREATED"
    REJECTED = "REJECTED"
    PUBLISHED = "PUBLISHED"
