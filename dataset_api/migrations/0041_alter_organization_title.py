# Generated by Django 4.0.7 on 2022-10-12 09:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dataset_api', '0040_remove_dataset_license_remove_dataset_access_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='organization',
            name='title',
            field=models.CharField(max_length=100, unique=True),
        ),
    ]
