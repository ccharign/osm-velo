# Generated by Django 4.0.2 on 2022-06-20 14:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dijk', '0009_typeamenity_amenity_horaires_amenity_id_osm_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='amenity',
            name='ville',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='dijk.ville'),
            preserve_default=False,
        ),
    ]
