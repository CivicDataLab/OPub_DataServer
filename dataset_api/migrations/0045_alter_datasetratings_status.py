# Generated by Django 4.0.7 on 2022-10-14 14:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dataset_api', '0044_organization_logo_alter_dataset_remote_issued'),
    ]

    operations = [
        migrations.AlterField(
            model_name='datasetratings',
            name='status',
            field=models.CharField(choices=[('CREATED', 'Created'), ('REJECTED', 'Rejected'), ('PUBLISHED', 'Published')], max_length=50),
        ),
    ]