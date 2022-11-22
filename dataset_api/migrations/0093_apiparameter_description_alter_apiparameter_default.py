# Generated by Django 4.0.7 on 2022-11-22 11:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dataset_api', '0092_datarequestparameter'),
    ]

    operations = [
        migrations.AddField(
            model_name='apiparameter',
            name='description',
            field=models.CharField(default='', max_length=500),
        ),
        migrations.AlterField(
            model_name='apiparameter',
            name='default',
            field=models.CharField(default='', max_length=500),
        ),
    ]