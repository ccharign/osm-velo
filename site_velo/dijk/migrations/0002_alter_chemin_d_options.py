# Generated by Django 3.2.7 on 2022-02-13 20:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dijk', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='chemin_d',
            options={'ordering': ['-dernier_p_modif']},
        ),
    ]
