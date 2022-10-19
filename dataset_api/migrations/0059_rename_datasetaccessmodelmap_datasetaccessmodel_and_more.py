# Generated by Django 4.0.7 on 2022-10-19 15:13

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dataset_api', '0058_datasetratings_user'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='DatasetAccessModelMap',
            new_name='DatasetAccessModel',
        ),
        migrations.RenameModel(
            old_name='DataAccessModelRequest',
            new_name='DatasetAccessModelRequest',
        ),
        migrations.RenameModel(
            old_name='AccessModelResource',
            new_name='DatasetAccessModelResource',
        ),
        migrations.RenameField(
            model_name='datarequest',
            old_name='data_access_model_request',
            new_name='dataset_access_model_request',
        ),
        migrations.RenameField(
            model_name='datasetaccessmodelresource',
            old_name='dataset_access_map',
            new_name='dataset_access_model',
        ),
    ]
