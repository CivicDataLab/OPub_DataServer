# Generated by Django 4.0.7 on 2022-11-01 21:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dataset_api', '0075_dataset_download_count'),
    ]

    operations = [
        migrations.AddField(
            model_name='datasetaccessmodelrequest',
            name='user_email',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
    ]
