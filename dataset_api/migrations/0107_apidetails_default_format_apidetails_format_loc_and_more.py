# Generated by Django 4.0.7 on 2022-11-27 10:27

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dataset_api', '0106_alter_resourceschema_unique_together_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='apidetails',
            name='default_format',
            field=models.CharField(default='', max_length=500),
        ),
        migrations.AddField(
            model_name='apidetails',
            name='format_loc',
            field=models.CharField(choices=[('HEADER', 'Header'), ('PARAM', 'Param')], default='', max_length=50),
        ),
        migrations.AddField(
            model_name='apidetails',
            name='supported_formats',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=25), blank=True, null=True, size=None),
        ),
        migrations.AddField(
            model_name='apiparameter',
            name='type',
            field=models.CharField(choices=[('EXPOSED', 'Exposed'), ('PAGINATION', 'Pagination')], default='EXPOSED', max_length=50),
            preserve_default=False,
        ),
    ]
