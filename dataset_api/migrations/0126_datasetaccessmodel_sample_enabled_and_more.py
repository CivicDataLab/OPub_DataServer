# Generated by Django 4.0.7 on 2022-12-21 15:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dataset_api', '0125_dataset_last_updated_dataset_published_date_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='datasetaccessmodel',
            name='sample_enabled',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='datasetaccessmodel',
            name='sample_rows',
            field=models.IntegerField(default=5),
        ),
    ]
