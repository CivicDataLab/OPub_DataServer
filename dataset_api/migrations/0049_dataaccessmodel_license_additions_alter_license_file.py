# Generated by Django 4.0.7 on 2022-10-16 18:16

import dataset_api.file_paths
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dataset_api', '0048_delete_apiresource'),
    ]

    operations = [
        migrations.AddField(
            model_name='dataaccessmodel',
            name='license_additions',
            field=models.ManyToManyField(blank=True, to='dataset_api.licenseaddition'),
        ),
        migrations.AlterField(
            model_name='license',
            name='file',
            field=models.FileField(blank=True, upload_to=dataset_api.file_paths._license_directory_path),
        ),
    ]
