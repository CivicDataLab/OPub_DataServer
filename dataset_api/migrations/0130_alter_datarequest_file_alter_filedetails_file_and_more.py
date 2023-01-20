# Generated by Django 4.0.7 on 2023-01-20 13:51

import dataset_api.file_paths
import django.core.files.storage
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dataset_api', '0129_geography_official_id_resourceschema_filterable_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='organization',
            name='organization_types',
            field=models.CharField(choices=[('STATE GOVERNMENT', 'State Government'), ('UNION_TERRITORY_GOVERNMENT', 'Union Territory Government'), ('URBAN_LOCAL_BODY', 'Urban Local Body'), ('ACADEMIC INSTITUTION', 'Academic Institution'), ('CENTRAL GOVERNMENT', 'Central Government'), ('CITIZENS GROUP', 'Citizens Group'), ('CIVIL SOCIETY ORGANISATION', 'Civil Society Organisation'), ('INDUSTRY BODY', 'Industry Body'), ('MEDIA ORGANISATION', 'Media Organisation'), ('OPEN DATA/TECHNOLOGY COMMUNITY', 'Open Data Technology Community'), ('PRIVATE COMPANY', 'Private Company'), ('PUBLIC SECTOR COMPANY', 'Public Sector Company'), ('OTHERS', 'Others'), ('STARTUP', 'Startup'), ('GOVERNMENT', 'Government'), ('CORPORATIONS', 'Corporations'), ('NGO', 'Ngo')], max_length=50),
        ),
    ]
