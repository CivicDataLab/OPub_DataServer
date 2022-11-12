from django.db import models


class LICENSEADDITIONSTATE(models.TextChoices):
    CREATED = "CREATED"
    REJECTED = "REJECTED"
    PUBLISHED = "PUBLISHED"
