# Generated by Django 3.2.7 on 2021-11-26 21:37

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dijk', '0003_rue_nœuds'),
    ]

    operations = [
        migrations.RenameField(
            model_name='rue',
            old_name='nœuds',
            new_name='nœuds_à_découper',
        ),
    ]
