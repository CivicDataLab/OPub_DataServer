# Generated by Django 4.0.7 on 2023-05-22 11:24

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dataset_api', '0169_license_dataset_type_policy_dataset_type_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='license',
            old_name='dataset_type',
            new_name='type',
        ),
        migrations.RenameField(
            model_name='policy',
            old_name='dataset_type',
            new_name='type',
        ),
    ]
