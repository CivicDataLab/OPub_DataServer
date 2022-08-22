# Generated by Django 4.0.6 on 2022-08-21 22:37

import dataset_api.models
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('dataset_api', '0002_rename_name_dataset_title'),
    ]

    operations = [
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('description', models.CharField(max_length=500)),
                ('issued', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('homepage', models.URLField(blank=True)),
                ('contact_email', models.EmailField(max_length=254)),
            ],
        ),
        migrations.AddField(
            model_name='dataset',
            name='License',
            field=models.CharField(default='not_specified', max_length=100),
        ),
        migrations.AddField(
            model_name='dataset',
            name='geography',
            field=models.CharField(default='Other', max_length=50),
        ),
        migrations.AddField(
            model_name='dataset',
            name='issued',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='dataset',
            name='modified',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='dataset',
            name='sector',
            field=models.CharField(default='Other', max_length=50),
        ),
        migrations.CreateModel(
            name='Resource',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('description', models.CharField(max_length=500)),
                ('issued', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField()),
                ('remote_url', models.URLField(blank=True)),
                ('file', models.FileField(blank=True, upload_to=dataset_api.models._resource_directory_path)),
                ('dataset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dataset_api.dataset')),
            ],
        ),
        migrations.CreateModel(
            name='Catalog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('description', models.CharField(max_length=500)),
                ('issued', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dataset_api.organization')),
            ],
        ),
        migrations.AddField(
            model_name='dataset',
            name='catalog',
            field=models.ForeignKey(default='', on_delete=django.db.models.deletion.CASCADE, to='dataset_api.catalog'),
            preserve_default=False,
        ),
    ]
