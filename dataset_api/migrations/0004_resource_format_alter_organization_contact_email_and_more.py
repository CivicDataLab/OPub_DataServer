# Generated by Django 4.0.6 on 2022-08-22 23:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dataset_api', '0003_organization_dataset_license_dataset_geography_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='resource',
            name='format',
            field=models.CharField(default='', max_length=15),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='organization',
            name='contact_email',
            field=models.EmailField(blank=True, max_length=254),
        ),
        migrations.AlterField(
            model_name='resource',
            name='modified',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
