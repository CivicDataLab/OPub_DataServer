from django.db import models


class RatingStatus(models.TextChoices):
    CREATED = "CREATED"
    REJECTED = "REJECTED"
    PUBLISHED = "PUBLISHED"


class LicenseStatus(models.TextChoices):
    CREATED = "CREATED"
    REJECTED = "REJECTED"
    PUBLISHED = "PUBLISHED"


class SubscriptionUnits(models.TextChoices):
    LIMITEDDOWNLOAD = "LIMITEDDOWNLOAD"
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    QUARTERLY = "QUARTERLY"
    MONTHLY = "MONTHLY"
    YEARLY = "YEARLY"


class OrganizationRequestStatusType(models.TextChoices):
    REQUESTED = "REQUESTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class OrganizationCreationStatusType(models.TextChoices):
    REQUESTED = "REQUESTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class OrganizationTypes(models.TextChoices):
    STARTUP = "STARTUP"
    GOVERNMENT = "GOVERNMENT"
    CORPORATIONS = "CORPORATIONS"
    NGO = "NGO"
