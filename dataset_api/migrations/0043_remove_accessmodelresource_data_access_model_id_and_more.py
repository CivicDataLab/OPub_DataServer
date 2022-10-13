# Generated by Django 4.0.6 on 2022-10-13 07:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dataset_api', '0042_accessmodelresource'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='accessmodelresource',
            name='data_access_model_id',
        ),
        migrations.RemoveField(
            model_name='dataaccessmodel',
            name='dataset',
        ),
        migrations.RemoveField(
            model_name='dataaccessmodel',
            name='resources',
        ),
        migrations.AddField(
            model_name='dataaccessmodel',
            name='organization',
            field=models.ForeignKey(default='', on_delete=django.db.models.deletion.CASCADE, to='dataset_api.organization'),
        ),
        migrations.CreateModel(
            name='DatasetAccessModelMap',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data_access_model', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dataset_api.dataaccessmodel')),
                ('dataset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dataset_api.dataset')),
            ],
        ),
        migrations.AddField(
            model_name='accessmodelresource',
            name='dataset_access_map',
            field=models.ForeignKey(default='', on_delete=django.db.models.deletion.CASCADE, to='dataset_api.datasetaccessmodelmap'),
        ),
    ]
