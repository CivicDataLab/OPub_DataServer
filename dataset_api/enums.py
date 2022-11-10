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


class ReviewType(models.TextChoices):
    REVIEW = "REVIEW"
    MODERATION = "MODERATION"


class AuthLocation(models.TextChoices):
    HEADER = "HEADER"
    PARAM = "PARAM"


class AuthType(models.TextChoices):
    CREDENTIALS = "CREDENTIALS"
    TOKEN = "TOKEN"
    NO_AUTH = "NO_AUTH"


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


class DataType(models.TextChoices):
    API = "API"
    FILE = "FILE"


class ValidationUnits(models.TextChoices):
    LIFETIME = "LIFETIME"
    PER_DAY = "PER_DAY"
    PER_WEEK = "PER_WEEK"
    PER_MONTH = "PER_MONTH"
    PER_YEAR = "PER_YEAR"