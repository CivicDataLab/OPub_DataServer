# Generated by Django 4.0.7 on 2022-10-15 13:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dataset_api', '0046_remove_license_organization_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dataaccessmodel',
            name='license',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dataset_api.license'),
        ),
    ]