# Generated by Django 4.0.2 on 2022-03-09 09:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dijk', '0003_chemin_d_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='cache_adresse',
            name='zone',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='dijk.zone'),
            preserve_default=False,
        ),
    ]