# Generated by Django 4.0.6 on 2022-09-12 22:22

import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dataset_api', '0017_apisource_apiresource'),
    ]

    operations = [
        migrations.CreateModel(
            name='APIResource',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('description', models.CharField(max_length=500)),
                ('issued', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('status', models.CharField(default='Draft', max_length=50)),
                ('masked_fields', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(blank=True, max_length=10), blank=True, null=True, size=None)),
                ('url_path', models.URLField()),
                ('auth_required', models.BooleanField()),
                ('response_type', models.CharField(max_length=20)),
                ('api_source', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dataset_api.apisource')),
                ('dataset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dataset_api.dataset')),
            ],
        ),
    ]
