# Generated by Django 4.0.7 on 2023-02-28 07:12

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dataset_api', '0149_remove_policy_data_access_model_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='dataaccessmodel',
            name='policy',
        ),
        migrations.AddField(
            model_name='datasetaccessmodel',
            name='policy',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='dataset_api.policy'),
        ),
    ]
