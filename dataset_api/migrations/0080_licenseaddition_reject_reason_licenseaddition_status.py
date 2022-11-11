# Generated by Django 4.0.7 on 2022-11-11 01:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dataset_api', '0079_alter_dataset_remote_modified'),
    ]

    operations = [
        migrations.AddField(
            model_name='licenseaddition',
            name='reject_reason',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AddField(
            model_name='licenseaddition',
            name='status',
            field=models.CharField(choices=[('CREATED', 'Created'), ('REJECTED', 'Rejected'), ('PUBLISHED', 'Published')], default='CREATED', max_length=50),
        ),
    ]