# Generated by Django 4.0.2 on 2022-03-11 15:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dijk', '0004_cache_adresse_zone'),
    ]

    operations = [
        migrations.CreateModel(
            name='CacheNomRue',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=200)),
                ('nom_osm', models.CharField(max_length=200)),
                ('zone', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dijk.zone')),
            ],
        ),
        migrations.AddConstraint(
            model_name='cachenomrue',
            constraint=models.UniqueConstraint(fields=('nom', 'zone'), name='Une seule entrée pour chaque (nom, zone).'),
        ),
    ]
