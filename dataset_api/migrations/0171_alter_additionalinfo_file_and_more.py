# Generated by Django 4.0.7 on 2023-05-25 02:43

import dataset_api.file_paths
import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dataset_api', '0170_rename_dataset_type_license_type_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='additionalinfo',
            name='file',
            field=models.FileField(blank=True, max_length=1000, upload_to=dataset_api.file_paths._info_directory_path),
        ),
    ]