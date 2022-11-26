# Generated by Django 4.0.7 on 2022-11-26 08:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dataset_api', '0098_organizationcreaterequest_username_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='apidetails',
            name='request_type',
            field=models.CharField(default='GET', max_length=20),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='apisource',
            name='auth_token_key',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
