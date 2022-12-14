# Generated by Django 4.0.6 on 2022-09-13 20:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dataset_api', '0019_datasetratings'),
    ]

    operations = [
        migrations.CreateModel(
            name='Sector',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=75)),
            ],
        ),
        migrations.AlterField(
            model_name='dataset',
            name='geography',
            field=models.ManyToManyField(blank=True, to='dataset_api.geography'),
        ),
    ]
