# Generated by Django 4.0.7 on 2023-03-12 09:53

import dataset_api.file_paths
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dataset_api', '0154_geography_parent_id_alter_datarequest_file_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='dataset',
            name='version_name',
            field=models.CharField(blank=True, default='Original', max_length=200, null=True),
        )
    ]