# Generated by Django 4.0.6 on 2022-09-19 23:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dataset_api', '0026_alter_datarequest_file'),
    ]

    operations = [
        migrations.AddField(
            model_name='datarequest',
            name='api_resource',
            field=models.ManyToManyField(to='dataset_api.apiresource'),
        ),
    ]
