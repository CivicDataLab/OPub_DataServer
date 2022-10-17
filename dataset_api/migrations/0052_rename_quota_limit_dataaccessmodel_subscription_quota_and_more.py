# Generated by Django 4.0.7 on 2022-10-17 08:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dataset_api', '0051_dataaccessmodel_subscription_model'),
    ]

    operations = [
        migrations.RenameField(
            model_name='dataaccessmodel',
            old_name='quota_limit',
            new_name='subscription_quota',
        ),
        migrations.RemoveField(
            model_name='dataaccessmodel',
            name='quota_limit_unit',
        ),
        migrations.RemoveField(
            model_name='dataaccessmodel',
            name='subscription_model',
        ),
        migrations.AddField(
            model_name='dataaccessmodel',
            name='subscription_quota_unit',
            field=models.CharField(choices=[('LIMITEDDOWNLOAD', 'Limiteddownload'), ('DAILY', 'Daily'), ('WEEKLY', 'Weekly'), ('QUARTERLY', 'Quarterly'), ('MONTHLY', 'Monthly'), ('YEARLY', 'Yearly')], default='DAILY', max_length=50),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='dataaccessmodel',
            name='rate_limit',
            field=models.IntegerField(blank=True),
        ),
        migrations.AlterField(
            model_name='dataaccessmodel',
            name='rate_limit_unit',
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
