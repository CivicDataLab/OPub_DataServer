# Generated by Django 4.0.7 on 2022-11-16 07:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dataset_api', '0086_dataset_confirms_to_dataset_contact_point_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='filedetails',
            name='format',
            field=models.CharField(max_length=50),
        ),
    ]
