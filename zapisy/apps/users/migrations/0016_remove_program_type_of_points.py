# Generated by Django 2.1.8 on 2019-05-17 16:37

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0015_merge_20190321_1311'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='program',
            name='type_of_points',
        ),
    ]