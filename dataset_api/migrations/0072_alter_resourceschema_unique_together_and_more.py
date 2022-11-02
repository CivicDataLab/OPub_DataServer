# Generated by Django 4.0.7 on 2022-10-31 15:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dataset_api', '0071_alter_resourceschema_unique_together'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='resourceschema',
            unique_together=set(),
        ),
        migrations.AlterField(
            model_name='resourceschema',
            name='array_field',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='array_item', to='dataset_api.resourceschema'),
        ),
        migrations.AlterField(
            model_name='resourceschema',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='parent_field', to='dataset_api.resourceschema'),
        ),
        migrations.AlterField(
            model_name='resourceschema',
            name='resource',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='dataset_api.resource'),
        ),
        migrations.AlterUniqueTogether(
            name='resourceschema',
            unique_together={('resource', 'key')},
        ),
    ]