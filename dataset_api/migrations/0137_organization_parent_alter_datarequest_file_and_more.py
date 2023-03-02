# Generated by Django 4.0.7 on 2023-02-13 12:47

import dataset_api.file_paths
import django.core.files.storage
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dataset_api', '0136_organizationcreaterequest_dpa_email_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='parent_field', to='dataset_api.organization'),
        ),
    ]