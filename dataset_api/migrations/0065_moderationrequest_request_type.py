@@ -0,0 +1,18 @@
 # Generated by Django 4.0.7 on 2022-10-17 11:28

 from django.db import migrations, models


 class Migration(migrations.Migration):

     dependencies = [
         ('dataset_api', '0064_remove_dataset_remark'),
     ]

     operations = [
         migrations.AddField(
             model_name='moderationrequest',
             name='request_type',
             field=models.CharField(choices=[('REVIEW', 'Review'), ('MODERATION', 'Moderation')], default='REVIEW', max_length=50),
         ),
     ]