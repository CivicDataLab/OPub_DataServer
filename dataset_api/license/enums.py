from django.db import models


class LicenseStatus(models.TextChoices):
    CREATED = "CREATED"
    REJECTED = "REJECTED"
    PUBLISHED = "PUBLISHED"


class AgreementStatus(models.TextChoices):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
