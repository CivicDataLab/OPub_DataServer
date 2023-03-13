from django.db import models


class PAYMENTTYPES(models.TextChoices):
    FREE = "FREE"
    PAID = "PAID"
