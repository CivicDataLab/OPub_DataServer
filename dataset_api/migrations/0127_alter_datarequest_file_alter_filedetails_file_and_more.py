# Generated by Django 4.0.7 on 2022-12-21 06:31

import dataset_api.file_paths
import django.core.files.storage
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dataset_api', '0126_resourceschema_filterable_alter_datarequest_file_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resourceschema',
            name='filterable',
            field=models.BooleanField(default=True),
        ),
    ]
