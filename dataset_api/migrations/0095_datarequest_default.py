# Generated by Django 4.0.7 on 2022-11-23 06:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dataset_api', '0094_apisource_organization'),
    ]

    operations = [
        migrations.AddField(
            model_name='datarequest',
            name='default',
            field=models.BooleanField(db_index=True, default=True),
            preserve_default=False,
        ),
    ]
