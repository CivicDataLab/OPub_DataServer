# Generated by Django 4.0.6 on 2022-10-04 05:00

import dataset_api.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dataset_api', '0033_filedetails_remote_url'),
    ]

    operations = [
        migrations.CreateModel(
            name='License',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('description', models.CharField(max_length=500)),
                ('issued', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('remote_url', models.URLField(blank=True)),
                ('file', models.FileField(blank=True, upload_to=dataset_api.models._contract_directory_path)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dataset_api.organization')),
            ],
        ),
        migrations.CreateModel(
            name='DataAccessModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('type', models.CharField(default='OPEN', max_length=100)),
                ('description', models.CharField(max_length=500)),
                ('issued', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('contract_url', models.URLField(blank=True)),
                ('contract', models.FileField(blank=True, upload_to=dataset_api.models._contract_directory_path)),
                ('license', models.CharField(default='not_specified', max_length=100)),
                ('quota_limit', models.IntegerField()),
                ('quota_limit_unit', models.CharField(max_length=100)),
                ('rate_limit', models.IntegerField()),
                ('rate_limit_unit', models.CharField(max_length=100)),
                ('dataset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dataset_api.dataset')),
                ('resources', models.ManyToManyField(to='dataset_api.resource')),
            ],
        ),
    ]