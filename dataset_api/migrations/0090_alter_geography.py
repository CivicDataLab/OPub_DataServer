# Generated by Django 4.0.7 on 2022-11-22 06:57

from django.db import migrations, models
import pathlib


class Migration(migrations.Migration):

    dependencies = [
        ('dataset_api', '0089_alter_licenseaddition_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='geography',
            name='name',
            field=models.CharField(max_length=75, unique=True),
        ),
    ]
