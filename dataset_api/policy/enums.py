from django.db import models


class PolicyStatus(models.TextChoices):
    REQUESTED = "REQUESTED"
    REJECTED = "REJECTED"
    PUBLISHED = "PUBLISHED"


# class AgreementStatus(models.TextChoices):
#     ACCEPTED = "ACCEPTED"
#     REJECTED = "REJECTED"
