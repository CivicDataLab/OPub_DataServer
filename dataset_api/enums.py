from enum import Enum
from django.db import models


class RatingStatus(models.TextChoices):
    CREATED = "CREATED"
    REJECTED = "REJECTED"
    PUBLISHED = "PUBLISHED"


class LicenseStatus(models.TextChoices):
    CREATED = "CREATED"
    REJECTED = "REJECTED"
    PUBLISHED = "PUBLISHED"


class SubscriptionModels(models.TextChoices):
    ONETIMEDOWNLOAD = "ONETIMEDOWNLOAD"
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    QUARTERLY = "QUARTERLY"
    MONTHLY = "MONTHLY"
    YEARLY = "YEARLY"
