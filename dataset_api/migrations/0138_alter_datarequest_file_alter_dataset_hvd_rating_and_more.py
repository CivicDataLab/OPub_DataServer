# Generated by Django 4.0.7 on 2023-02-13 13:43

import dataset_api.file_paths
import django.core.files.storage
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dataset_api', '0137_organization_parent_alter_datarequest_file_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dataset',
            name='hvd_rating',
            field=models.DecimalField(decimal_places=2, max_digits=4),
        ),
    ]