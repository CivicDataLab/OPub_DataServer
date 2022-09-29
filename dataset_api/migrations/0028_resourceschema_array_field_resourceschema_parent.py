# Generated by Django 4.0.6 on 2022-09-26 15:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dataset_api', '0027_datarequest_api_resource'),
    ]

    operations = [
        migrations.AddField(
            model_name='resourceschema',
            name='array_field',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='array_item', to='dataset_api.resourceschema'),
        ),
        migrations.AddField(
            model_name='resourceschema',
            name='parent',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='parent_field', to='dataset_api.resourceschema'),
        ),
    ]