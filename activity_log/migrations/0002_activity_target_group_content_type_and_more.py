# Generated by Django 4.0.7 on 2022-10-24 07:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('activity_log', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='activity',
            name='target_group_content_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='target_group', to='contenttypes.contenttype'),
        ),
        migrations.AddField(
            model_name='activity',
            name='target_group_object_id',
            field=models.CharField(blank=True, db_index=True, max_length=255, null=True),
        ),
    ]