# Generated by Django 4.0.7 on 2022-11-24 08:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dataset_api', '0096_alter_datarequest_default_subscribe'),
    ]

    operations = [
        migrations.AddField(
            model_name='resourceschema',
            name='display_name',
            field=models.CharField(default='', max_length=100),
            preserve_default=False,
        ),
    ]
