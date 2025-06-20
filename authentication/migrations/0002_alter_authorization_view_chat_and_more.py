# Generated by Django 5.2 on 2025-04-27 13:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='authorization',
            name='view_chat',
            field=models.CharField(choices=[('Yes', 'Yes'), ('No', 'No')], default='No', max_length=50),
        ),
        migrations.AlterField(
            model_name='authorization',
            name='view_dashboard',
            field=models.CharField(choices=[('Yes', 'Yes'), ('No', 'No')], default='No', max_length=50),
        ),
        migrations.AlterField(
            model_name='authorization',
            name='view_logs',
            field=models.CharField(choices=[('Yes', 'Yes'), ('No', 'No')], default='No', max_length=50),
        ),
        migrations.AlterField(
            model_name='authorization',
            name='view_message',
            field=models.CharField(choices=[('Yes', 'Yes'), ('No', 'No')], default='No', max_length=50),
        ),
        migrations.AlterField(
            model_name='authorization',
            name='view_setting',
            field=models.CharField(choices=[('Yes', 'Yes'), ('No', 'No')], default='No', max_length=50),
        ),
    ]
