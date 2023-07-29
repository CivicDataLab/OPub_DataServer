# Generated by Django 4.0.7 on 2023-03-23 10:20

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dataset_api', '0160_alter_datasetaccessmodelrequest_token_time_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='datasetaccessmodelrequest',
            name='token_time',
            field=models.DateTimeField(default=datetime.datetime(2023, 3, 23, 10, 20, 33, 553138)),
        ),
        migrations.AlterField(
            model_name='orgdpahistory',
            name='old_dpa',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]