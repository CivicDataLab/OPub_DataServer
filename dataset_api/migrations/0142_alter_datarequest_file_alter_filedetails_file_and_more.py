# Generated by Django 4.0.7 on 2023-02-18 10:45

import dataset_api.file_paths
import django.core.files.storage
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dataset_api', '0141_organizationcreaterequest_address_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='organizationcreaterequest',
            name='status',
            field=models.CharField(choices=[('REQUESTED', 'Requested'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected'), ('DELETED', 'Deleted')], max_length=20),
        ),
        migrations.AlterField(
            model_name='organizationrequest',
            name='status',
            field=models.CharField(choices=[('REQUESTED', 'Requested'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected'), ('DELETED', 'Deleted')], max_length=20),
        ),
    ]