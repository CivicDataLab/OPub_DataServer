# Generated by Django 4.0.7 on 2023-02-10 06:42

import dataset_api.file_paths
import django.core.files.storage
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dataset_api', '0133_dataaccessmodel_is_global_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='organizationcreaterequest',
            name='data_description',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
    ]