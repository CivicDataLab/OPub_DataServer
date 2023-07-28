# Generated by Django 4.0.7 on 2023-05-03 10:41

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dataset_api', '0164_alter_datasetaccessmodelrequest_token_time'),
    ]

    operations = [
        migrations.AddField(
            model_name='resource',
            name='external_url',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='dataset',
            name='dataset_type',
            field=models.CharField(choices=[('API', 'Api'), ('FILE', 'File'), ('EXT', 'External')], default='FILE', max_length=50),
        ),
    ]
