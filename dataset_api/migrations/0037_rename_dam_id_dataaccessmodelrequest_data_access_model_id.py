# Generated by Django 4.0.6 on 2022-10-05 17:13

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dataset_api', '0036_alter_dataaccessmodel_contract_url_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='dataaccessmodelrequest',
            old_name='dam_id',
            new_name='data_access_model_id',
        ),
    ]
