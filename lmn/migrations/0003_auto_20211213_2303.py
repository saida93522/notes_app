# Generated by Django 3.1.2 on 2021-12-14 05:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lmn', '0002_auto_20211213_2214'),
    ]

    operations = [
        migrations.AlterField(
            model_name='artist',
            name='name',
            field=models.CharField(max_length=200, unique=True),
        ),
    ]