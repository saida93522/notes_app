# Generated by Django 3.1.2 on 2021-12-13 23:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lmn', '0005_auto_20211214_1537'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='avatar',
            field=models.ImageField(blank=True, default='default.jpg', null=True, upload_to='profile_images'),
        ),
    ]
