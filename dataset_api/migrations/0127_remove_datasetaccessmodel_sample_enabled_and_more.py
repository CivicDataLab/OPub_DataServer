# Generated by Django 4.0.7 on 2022-12-21 15:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dataset_api', '0126_datasetaccessmodel_sample_enabled_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='datasetaccessmodel',
            name='sample_enabled',
        ),
        migrations.RemoveField(
            model_name='datasetaccessmodel',
            name='sample_rows',
        ),
        migrations.AddField(
            model_name='datasetaccessmodelresource',
            name='sample_enabled',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='datasetaccessmodelresource',
            name='sample_rows',
            field=models.IntegerField(default=5),
        ),
    ]
