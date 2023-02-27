from django.db import models


class PolicyStatus(models.TextChoices):
    CREATED = "CREATED"
    REJECTED = "REJECTED"
    PUBLISHED = "PUBLISHED"


# class AgreementStatus(models.TextChoices):
#     ACCEPTED = "ACCEPTED"
#     REJECTED = "REJECTED"
