# Generated by Django 4.0.7 on 2023-03-07 14:27

import dataset_api.file_paths
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dataset_api', '0153_sector_parent_id_alter_datarequest_file_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='geography',
            name='parent_id',
            field=models.ForeignKey(blank=True, default='', null=True, on_delete=django.db.models.deletion.CASCADE, to='dataset_api.geography'),
        ),
    ]